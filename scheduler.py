import schedule
import time
import asyncio
import pytz
from datetime import datetime, timedelta
import logging
from threading import Thread
from market_analyzer import MarketAnalyzer
from strategy_engine import StrategyEngine
from trading_interface import TradingInterface, PaperTradingInterface
from risk_management import RiskManager
from config import Config

class TradingScheduler:
    def __init__(self, use_paper_trading=True):
        self.config = Config()
        self.use_paper_trading = use_paper_trading
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer()
        self.strategy_engine = StrategyEngine()
        self.risk_manager = RiskManager()
        
        # Choose trading interface
        if use_paper_trading:
            self.trading_interface = PaperTradingInterface()
        else:
            self.trading_interface = TradingInterface()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Trading state
        self.is_trading_day = True
        self.market_analysis_complete = False
        self.trades_executed_today = []
        
    def setup_schedule(self):
        """Set up the trading schedule"""
        # Reset daily metrics at market open (6:30 AM PST)
        schedule.every().day.at("06:30").do(self.reset_daily_metrics)
        
        # Main market analysis at 7:00 AM PST
        schedule.every().day.at("07:00").do(self.run_market_analysis_and_trade)
        
        # Additional analysis checks throughout the day
        schedule.every().day.at("09:00").do(self.check_market_conditions)
        schedule.every().day.at("11:00").do(self.check_market_conditions)
        schedule.every().day.at("13:00").do(self.check_market_conditions)
        
        # Position monitoring every 30 minutes during market hours
        schedule.every(30).minutes.do(self.monitor_positions)
        
        # End of day cleanup at 4:00 PM PST
        schedule.every().day.at("16:00").do(self.end_of_day_cleanup)
        
        self.logger.info("Trading schedule set up successfully")
    
    def is_market_day(self):
        """Check if today is a trading day (weekday)"""
        today = datetime.now(pytz.timezone('US/Pacific'))
        return today.weekday() < 5  # Monday = 0, Friday = 4
    
    def is_market_hours(self):
        """Check if current time is within market hours (6:30 AM - 4:00 PM PST)"""
        now = datetime.now(pytz.timezone('US/Pacific'))
        market_open = now.replace(hour=6, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def reset_daily_metrics(self):
        """Reset daily metrics at the start of each trading day"""
        if not self.is_market_day():
            return
            
        self.logger.info("Resetting daily metrics for new trading day")
        self.risk_manager.reset_daily_metrics()
        self.market_analysis_complete = False
        self.trades_executed_today = []
        
        # Connect to trading interface
        asyncio.run(self.connect_trading_interface())
    
    async def connect_trading_interface(self):
        """Connect to the trading interface"""
        try:
            connected = await self.trading_interface.connect()
            if connected:
                self.logger.info("Successfully connected to trading interface")
            else:
                self.logger.error("Failed to connect to trading interface")
        except Exception as e:
            self.logger.error(f"Error connecting to trading interface: {e}")
    
    def run_market_analysis_and_trade(self):
        """Main function to analyze market and execute trades at 7 AM PST"""
        if not self.is_market_day():
            self.logger.info("Not a trading day, skipping analysis")
            return
            
        self.logger.info("Starting 7 AM market analysis and trading routine")
        
        try:
            # Run market analysis
            market_analysis = self.market_analyzer.get_market_analysis()
            
            if market_analysis is None:
                self.logger.error("Failed to get market analysis")
                return
            
            self.logger.info(f"Market Analysis Complete:")
            self.logger.info(f"Direction: {market_analysis['direction']}")
            self.logger.info(f"SPX Price: ${market_analysis['spx_price']:.2f}")
            self.logger.info(f"VIX Level: {market_analysis['vix_level']:.1f}")
            self.logger.info(f"RSI: {market_analysis['rsi']:.1f}")
            
            # Generate trade recommendations
            recommendations = self.strategy_engine.generate_trade_recommendations(market_analysis)
            
            if not recommendations:
                self.logger.info("No trade recommendations generated")
                self.market_analysis_complete = True
                return
            
            # Execute trades
            asyncio.run(self.execute_recommended_trades(recommendations))
            self.market_analysis_complete = True
            
        except Exception as e:
            self.logger.error(f"Error in market analysis and trading: {e}")
    
    async def execute_recommended_trades(self, recommendations):
        """Execute recommended trades with risk management"""
        account_info = await self.trading_interface.get_account_info()
        
        for trade in recommendations:
            try:
                # Format and log trade summary
                trade_summary = self.strategy_engine.format_trade_summary(trade)
                self.logger.info(f"Trade Recommendation:\n{trade_summary}")
                
                # Risk management validation
                validation = self.risk_manager.validate_trade(
                    trade, account_info, self.trades_executed_today
                )
                
                if not validation['approved']:
                    self.logger.warning(f"Trade rejected: {', '.join(validation['reasons'])}")
                    continue
                
                if validation['warnings']:
                    self.logger.warning(f"Trade warnings: {', '.join(validation['warnings'])}")
                
                # Check if we should stop trading
                should_stop, reason = self.risk_manager.should_stop_trading(account_info)
                if should_stop:
                    self.logger.warning(f"Stopping trading: {reason}")
                    break
                
                # Execute the trade
                if trade['recommendation'] == 'EXECUTE':
                    success = await self.trading_interface.execute_trade(trade)
                    
                    if success:
                        self.trades_executed_today.append(trade)
                        self.risk_manager.update_daily_metrics(new_trade=True)
                        self.logger.info(f"Trade executed successfully: {trade['strategy']}")
                    else:
                        self.logger.error(f"Failed to execute trade: {trade['strategy']}")
                else:
                    self.logger.info(f"Trade marked as MONITOR only: {trade['strategy']}")
                    
            except Exception as e:
                self.logger.error(f"Error executing trade: {e}")
    
    def check_market_conditions(self):
        """Check market conditions and potentially adjust positions"""
        if not self.is_market_day() or not self.is_market_hours():
            return
            
        if not self.market_analysis_complete:
            return
            
        try:
            # Get updated market analysis
            current_analysis = self.market_analyzer.get_market_analysis()
            
            if current_analysis:
                self.logger.info(f"Market Check - Direction: {current_analysis['direction']}, "
                               f"SPX: ${current_analysis['spx_price']:.2f}, "
                               f"VIX: {current_analysis['vix_level']:.1f}")
                
                # Check if market conditions have changed significantly
                # This could trigger position adjustments or new trades
                # Implementation depends on specific strategy requirements
                
        except Exception as e:
            self.logger.error(f"Error in market condition check: {e}")
    
    def monitor_positions(self):
        """Monitor open positions"""
        if not self.is_market_day() or not self.is_market_hours():
            return
            
        try:
            asyncio.run(self.trading_interface.monitor_positions())
            
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            self.logger.info(f"Risk Summary: Daily P&L: ${risk_summary['daily_pnl']:.2f}, "
                           f"Trades Today: {risk_summary['trades_today']}")
            
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
    
    def end_of_day_cleanup(self):
        """End of day cleanup and reporting"""
        if not self.is_market_day():
            return
            
        try:
            self.logger.info("Running end of day cleanup")
            
            # Get final risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Log daily summary
            self.logger.info("=== DAILY TRADING SUMMARY ===")
            self.logger.info(f"Trades Executed: {len(self.trades_executed_today)}")
            self.logger.info(f"Daily P&L: ${risk_summary['daily_pnl']:.2f}")
            self.logger.info(f"Total Trades: {risk_summary['trades_today']}")
            
            # Disconnect from trading interface
            self.trading_interface.disconnect()
            
        except Exception as e:
            self.logger.error(f"Error in end of day cleanup: {e}")
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        def scheduler_thread():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = Thread(target=scheduler_thread, daemon=True)
        scheduler_thread.start()
        self.logger.info("Scheduler thread started")
        
        return scheduler_thread
    
    def run_manual_analysis(self):
        """Run manual market analysis for testing"""
        self.logger.info("Running manual market analysis")
        self.run_market_analysis_and_trade()
    
    def start_bot(self):
        """Start the trading bot"""
        self.logger.info("Starting SPX 0DTE Trading Bot")
        self.logger.info(f"Paper Trading Mode: {self.use_paper_trading}")
        
        # Set up schedule
        self.setup_schedule()
        
        # Start scheduler
        scheduler_thread = self.run_scheduler()
        
        self.logger.info("Trading bot started successfully")
        self.logger.info("Press Ctrl+C to stop the bot")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down trading bot...")
            self.trading_interface.disconnect()
            self.logger.info("Trading bot stopped")

if __name__ == "__main__":
    # Create and start the trading bot
    bot = TradingScheduler(use_paper_trading=True)
    bot.start_bot()