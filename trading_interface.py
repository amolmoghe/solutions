import asyncio
from ib_insync import *
import pandas as pd
from datetime import datetime, timedelta
import logging
from config import Config

class TradingInterface:
    def __init__(self):
        self.config = Config()
        self.ib = IB()
        self.connected = False
        self.positions = {}
        self.orders = {}
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Connect to Interactive Brokers"""
        try:
            await self.ib.connectAsync(
                host=self.config.IB_HOST, 
                port=self.config.IB_PORT, 
                clientId=self.config.IB_CLIENT_ID
            )
            self.connected = True
            self.logger.info("Connected to Interactive Brokers")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to IB: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from Interactive Brokers")
    
    def create_spx_option_contract(self, strike, expiry, option_type, exchange='SMART'):
        """Create SPX option contract"""
        contract = Option(
            symbol='SPX',
            lastTradeDateOrContractMonth=expiry,
            strike=strike,
            right=option_type.upper(),
            exchange=exchange,
            currency='USD'
        )
        return contract
    
    def create_put_credit_spread_order(self, trade_data, quantity=1):
        """Create put credit spread order"""
        try:
            # Create option contracts
            short_put = self.create_spx_option_contract(
                trade_data['short_strike'], 
                trade_data['expiry'], 
                'PUT'
            )
            long_put = self.create_spx_option_contract(
                trade_data['long_strike'], 
                trade_data['expiry'], 
                'PUT'
            )
            
            # Create combo contract for spread
            combo = Contract()
            combo.symbol = 'SPX'
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            # Define legs
            leg1 = ComboLeg()
            leg1.conId = short_put.conId if hasattr(short_put, 'conId') else 0
            leg1.ratio = 1
            leg1.action = 'SELL'
            leg1.exchange = 'SMART'
            
            leg2 = ComboLeg()
            leg2.conId = long_put.conId if hasattr(long_put, 'conId') else 0
            leg2.ratio = 1
            leg2.action = 'BUY'
            leg2.exchange = 'SMART'
            
            combo.comboLegs = [leg1, leg2]
            
            # Create order
            order = Order()
            order.action = 'BUY'  # Buying the spread (net credit)
            order.totalQuantity = quantity
            order.orderType = 'LMT'
            order.lmtPrice = trade_data['net_credit'] * 0.95  # 5% below theoretical
            order.tif = 'DAY'
            
            return combo, order
            
        except Exception as e:
            self.logger.error(f"Error creating put credit spread order: {e}")
            return None, None
    
    def create_call_diagonal_order(self, trade_data, quantity=1):
        """Create call diagonal spread order"""
        try:
            # Create option contracts
            short_call = self.create_spx_option_contract(
                trade_data['short_strike'], 
                trade_data['short_expiry'], 
                'CALL'
            )
            long_call = self.create_spx_option_contract(
                trade_data['long_strike'], 
                trade_data['long_expiry'], 
                'CALL'
            )
            
            # Create combo contract for diagonal spread
            combo = Contract()
            combo.symbol = 'SPX'
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            # Define legs
            leg1 = ComboLeg()
            leg1.conId = short_call.conId if hasattr(short_call, 'conId') else 0
            leg1.ratio = 1
            leg1.action = 'SELL'
            leg1.exchange = 'SMART'
            
            leg2 = ComboLeg()
            leg2.conId = long_call.conId if hasattr(long_call, 'conId') else 0
            leg2.ratio = 1
            leg2.action = 'BUY'
            leg2.exchange = 'SMART'
            
            combo.comboLegs = [leg1, leg2]
            
            # Create order
            order = Order()
            order.action = 'BUY'  # Buying the diagonal spread (net debit)
            order.totalQuantity = quantity
            order.orderType = 'LMT'
            order.lmtPrice = trade_data['net_debit'] * 1.05  # 5% above theoretical
            order.tif = 'DAY'
            
            return combo, order
            
        except Exception as e:
            self.logger.error(f"Error creating call diagonal order: {e}")
            return None, None
    
    def create_iron_condor_order(self, trade_data, quantity=1):
        """Create iron condor order (4-leg spread)"""
        try:
            # Create all four option contracts
            short_put = self.create_spx_option_contract(
                trade_data['short_put_strike'], 
                trade_data['expiry'], 
                'PUT'
            )
            long_put = self.create_spx_option_contract(
                trade_data['long_put_strike'], 
                trade_data['expiry'], 
                'PUT'
            )
            short_call = self.create_spx_option_contract(
                trade_data['short_call_strike'], 
                trade_data['expiry'], 
                'CALL'
            )
            long_call = self.create_spx_option_contract(
                trade_data['long_call_strike'], 
                trade_data['expiry'], 
                'CALL'
            )
            
            # Create combo contract for iron condor
            combo = Contract()
            combo.symbol = 'SPX'
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            # Define all four legs
            leg1 = ComboLeg()  # Short Put
            leg1.conId = short_put.conId if hasattr(short_put, 'conId') else 0
            leg1.ratio = 1
            leg1.action = 'SELL'
            leg1.exchange = 'SMART'
            
            leg2 = ComboLeg()  # Long Put
            leg2.conId = long_put.conId if hasattr(long_put, 'conId') else 0
            leg2.ratio = 1
            leg2.action = 'BUY'
            leg2.exchange = 'SMART'
            
            leg3 = ComboLeg()  # Short Call
            leg3.conId = short_call.conId if hasattr(short_call, 'conId') else 0
            leg3.ratio = 1
            leg3.action = 'SELL'
            leg3.exchange = 'SMART'
            
            leg4 = ComboLeg()  # Long Call
            leg4.conId = long_call.conId if hasattr(long_call, 'conId') else 0
            leg4.ratio = 1
            leg4.action = 'BUY'
            leg4.exchange = 'SMART'
            
            combo.comboLegs = [leg1, leg2, leg3, leg4]
            
            # Create order
            order = Order()
            order.action = 'BUY'  # Buying the iron condor (net credit)
            order.totalQuantity = quantity
            order.orderType = 'LMT'
            order.lmtPrice = trade_data['net_credit'] * 0.95  # 5% below theoretical
            order.tif = 'DAY'
            
            return combo, order
            
        except Exception as e:
            self.logger.error(f"Error creating iron condor order: {e}")
            return None, None
    
    async def place_order(self, contract, order):
        """Place order with Interactive Brokers"""
        if not self.connected:
            self.logger.error("Not connected to IB")
            return None
            
        try:
            trade = self.ib.placeOrder(contract, order)
            self.logger.info(f"Order placed: {trade}")
            return trade
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
    
    async def get_option_chain(self, symbol='SPX', expiry=None):
        """Get option chain data"""
        if not self.connected:
            return None
            
        try:
            # Create underlying contract
            stock = Stock(symbol, 'SMART', 'USD')
            
            # Get option chain
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock.symbol, '', stock.secType, stock.conId
            )
            
            if chains:
                chain = chains[0]
                strikes = chain.strikes
                expirations = chain.expirations
                
                return {
                    'strikes': strikes,
                    'expirations': expirations
                }
        except Exception as e:
            self.logger.error(f"Error getting option chain: {e}")
            return None
    
    async def get_market_data(self, contract):
        """Get real-time market data for contract"""
        if not self.connected:
            return None
            
        try:
            ticker = self.ib.reqMktData(contract)
            await asyncio.sleep(2)  # Wait for data
            
            return {
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last,
                'volume': ticker.volume
            }
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return None
    
    async def get_positions(self):
        """Get current positions"""
        if not self.connected:
            return []
            
        try:
            positions = self.ib.positions()
            return positions
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_info(self):
        """Get account information"""
        if not self.connected:
            return None
            
        try:
            account_values = self.ib.accountValues()
            account_info = {}
            
            for value in account_values:
                if value.tag in ['NetLiquidation', 'AvailableFunds', 'BuyingPower']:
                    account_info[value.tag] = float(value.value)
                    
            return account_info
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def calculate_position_size(self, trade_data, account_info, risk_percent=0.02):
        """Calculate position size based on account size and risk"""
        try:
            if account_info is None:
                return 1
                
            account_value = account_info.get('NetLiquidation', 100000)
            max_risk = account_value * risk_percent
            
            trade_risk = trade_data.get('max_loss', 1000)
            
            if trade_risk > 0:
                position_size = int(max_risk / trade_risk)
                return max(1, min(position_size, 10))  # Between 1 and 10 contracts
            
            return 1
        except:
            return 1
    
    async def execute_trade(self, trade_data):
        """Execute trade based on strategy"""
        if not self.connected:
            self.logger.error("Not connected to IB")
            return False
            
        try:
            # Get account info for position sizing
            account_info = await self.get_account_info()
            quantity = self.calculate_position_size(trade_data, account_info)
            
            if trade_data['strategy'] == 'put_credit_spread':
                contract, order = self.create_put_credit_spread_order(trade_data, quantity)
            elif trade_data['strategy'] == 'call_diagonal':
                contract, order = self.create_call_diagonal_order(trade_data, quantity)
            elif trade_data['strategy'] == 'iron_condor':
                contract, order = self.create_iron_condor_order(trade_data, quantity)
            else:
                self.logger.error(f"Unknown strategy: {trade_data['strategy']}")
                return False
            
            if contract and order:
                trade = await self.place_order(contract, order)
                if trade:
                    self.logger.info(f"Trade executed successfully: {trade_data['strategy']}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False
    
    async def monitor_positions(self):
        """Monitor open positions"""
        if not self.connected:
            return
            
        try:
            positions = await self.get_positions()
            
            for position in positions:
                if 'SPX' in str(position.contract.symbol):
                    self.logger.info(f"SPX Position: {position}")
                    
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")

# Paper trading simulation class for testing
class PaperTradingInterface:
    def __init__(self):
        self.config = Config()
        self.positions = []
        self.orders = []
        self.account_balance = 100000  # Starting with $100k
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Simulate connection"""
        self.logger.info("Connected to Paper Trading")
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.logger.info("Disconnected from Paper Trading")
    
    async def execute_trade(self, trade_data):
        """Simulate trade execution"""
        try:
            # Simulate order fill
            order = {
                'strategy': trade_data['strategy'],
                'timestamp': datetime.now(),
                'status': 'FILLED',
                'quantity': 1,
                'fill_price': trade_data.get('net_credit', trade_data.get('net_debit', 0))
            }
            
            self.orders.append(order)
            self.positions.append(trade_data)
            
            self.logger.info(f"Paper trade executed: {trade_data['strategy']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in paper trading: {e}")
            return False
    
    async def get_account_info(self):
        """Return simulated account info"""
        return {
            'NetLiquidation': self.account_balance,
            'AvailableFunds': self.account_balance * 0.8,
            'BuyingPower': self.account_balance * 2
        }