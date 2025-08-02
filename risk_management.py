import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import Config
import logging

class RiskManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_daily_loss = 5000  # Maximum daily loss
        self.max_position_size = 10  # Maximum contracts per position
        self.max_portfolio_risk = 0.05  # 5% of account value
        self.max_correlation_exposure = 0.3  # Max 30% in correlated positions
        
        # Track daily metrics
        self.daily_pnl = 0
        self.trades_today = 0
        self.max_trades_per_day = 5
        
    def validate_trade(self, trade_data, account_info=None, existing_positions=None):
        """Comprehensive trade validation"""
        validation_results = {
            'approved': True,
            'reasons': [],
            'warnings': [],
            'recommended_size': 1
        }
        
        try:
            # 1. Basic trade validation
            if not self._validate_basic_requirements(trade_data):
                validation_results['approved'] = False
                validation_results['reasons'].append("Basic requirements not met")
            
            # 2. Probability of profit check
            if trade_data.get('prob_profit', 0) < self.config.MIN_PROBABILITY:
                validation_results['approved'] = False
                validation_results['reasons'].append(f"Probability of profit too low: {trade_data.get('prob_profit', 0):.1%}")
            
            # 3. Risk/reward validation
            if not self._validate_risk_reward(trade_data):
                validation_results['warnings'].append("Poor risk/reward ratio")
            
            # 4. Position sizing
            if account_info:
                recommended_size = self._calculate_position_size(trade_data, account_info)
                validation_results['recommended_size'] = recommended_size
                
                if recommended_size == 0:
                    validation_results['approved'] = False
                    validation_results['reasons'].append("Insufficient account size for minimum position")
            
            # 5. Daily limits check
            if not self._check_daily_limits():
                validation_results['approved'] = False
                validation_results['reasons'].append("Daily trading limits exceeded")
            
            # 6. Greeks validation
            if not self._validate_greeks(trade_data):
                validation_results['warnings'].append("Greeks outside preferred ranges")
            
            # 7. Market conditions check
            if not self._validate_market_conditions(trade_data):
                validation_results['warnings'].append("Market conditions not optimal")
            
            # 8. Concentration risk
            if existing_positions and not self._check_concentration_risk(trade_data, existing_positions):
                validation_results['approved'] = False
                validation_results['reasons'].append("Would exceed concentration limits")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in trade validation: {e}")
            validation_results['approved'] = False
            validation_results['reasons'].append("Validation error occurred")
            return validation_results
    
    def _validate_basic_requirements(self, trade_data):
        """Check basic trade requirements"""
        required_fields = ['strategy', 'max_loss', 'max_profit', 'prob_profit']
        
        for field in required_fields:
            if field not in trade_data:
                return False
        
        # Check for reasonable values
        if trade_data['max_loss'] <= 0 or trade_data['max_profit'] <= 0:
            return False
            
        if trade_data['prob_profit'] <= 0 or trade_data['prob_profit'] > 1:
            return False
            
        return True
    
    def _validate_risk_reward(self, trade_data):
        """Validate risk/reward ratio"""
        try:
            max_profit = trade_data.get('max_profit', 0)
            max_loss = trade_data.get('max_loss', 1)
            
            risk_reward_ratio = max_profit / max_loss
            
            # Different thresholds for different strategies
            if trade_data.get('strategy') == 'put_credit_spread':
                min_ratio = 0.2  # Credit spreads typically have lower ratios
            elif trade_data.get('strategy') == 'call_diagonal':
                min_ratio = 0.3  # Diagonals should have better ratios
            else:
                min_ratio = 0.25
                
            return risk_reward_ratio >= min_ratio
            
        except:
            return False
    
    def _calculate_position_size(self, trade_data, account_info):
        """Calculate optimal position size"""
        try:
            account_value = account_info.get('NetLiquidation', 100000)
            available_funds = account_info.get('AvailableFunds', account_value * 0.8)
            
            # Risk-based sizing
            max_risk_per_trade = account_value * 0.02  # 2% risk per trade
            trade_risk = trade_data.get('max_loss', 1000)
            
            risk_based_size = int(max_risk_per_trade / trade_risk) if trade_risk > 0 else 0
            
            # Capital-based sizing
            required_capital = trade_risk * 2  # Assume 2x margin requirement
            capital_based_size = int(available_funds / required_capital) if required_capital > 0 else 0
            
            # Take the minimum of both constraints
            optimal_size = min(risk_based_size, capital_based_size, self.max_position_size)
            
            return max(0, optimal_size)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 1
    
    def _check_daily_limits(self):
        """Check if daily trading limits are exceeded"""
        # Check daily loss limit
        if abs(self.daily_pnl) >= self.max_daily_loss:
            return False
            
        # Check number of trades
        if self.trades_today >= self.max_trades_per_day:
            return False
            
        return True
    
    def _validate_greeks(self, trade_data):
        """Validate option Greeks are within acceptable ranges"""
        try:
            # Delta validation
            net_delta = abs(trade_data.get('net_delta', 0))
            if net_delta > 0.5:  # Too much directional risk
                return False
            
            # Theta validation - should be positive for credit strategies
            net_theta = trade_data.get('net_theta', 0)
            if trade_data.get('strategy') == 'put_credit_spread' and net_theta <= 0:
                return False
            
            # Vega validation - limit volatility risk
            net_vega = abs(trade_data.get('net_vega', 0))
            if net_vega > 50:  # Too much vega risk
                return False
                
            return True
            
        except:
            return True  # Default to true if can't validate
    
    def _validate_market_conditions(self, trade_data):
        """Validate current market conditions are suitable"""
        try:
            vix_level = trade_data.get('vix_level', 20)
            rsi = trade_data.get('rsi', 50)
            strategy = trade_data.get('strategy')
            
            # VIX-based validation
            if strategy == 'put_credit_spread':
                # Prefer lower VIX for credit spreads
                if vix_level > 35:
                    return False
            elif strategy == 'call_diagonal':
                # Prefer moderate VIX for diagonals
                if vix_level < 15 or vix_level > 40:
                    return False
            
            # RSI validation
            if strategy == 'put_credit_spread':
                # Avoid oversold conditions
                if rsi < 30:
                    return False
            
            return True
            
        except:
            return True
    
    def _check_concentration_risk(self, trade_data, existing_positions):
        """Check if new trade would create concentration risk"""
        try:
            strategy = trade_data.get('strategy')
            
            # Count existing positions of same strategy
            same_strategy_count = sum(1 for pos in existing_positions 
                                    if pos.get('strategy') == strategy)
            
            # Limit concentration in single strategy
            if same_strategy_count >= 3:
                return False
            
            # Check total SPX exposure
            spx_positions = [pos for pos in existing_positions 
                           if 'SPX' in str(pos)]
            
            if len(spx_positions) >= 5:  # Max 5 SPX positions
                return False
                
            return True
            
        except:
            return True
    
    def update_daily_metrics(self, pnl_change=0, new_trade=False):
        """Update daily tracking metrics"""
        self.daily_pnl += pnl_change
        
        if new_trade:
            self.trades_today += 1
            
        self.logger.info(f"Daily P&L: ${self.daily_pnl:.2f}, Trades: {self.trades_today}")
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of each trading day)"""
        self.daily_pnl = 0
        self.trades_today = 0
        self.logger.info("Daily metrics reset")
    
    def get_risk_summary(self, account_info=None, positions=None):
        """Get comprehensive risk summary"""
        summary = {
            'daily_pnl': self.daily_pnl,
            'trades_today': self.trades_today,
            'daily_limit_remaining': self.max_daily_loss - abs(self.daily_pnl),
            'trades_remaining': self.max_trades_per_day - self.trades_today
        }
        
        if account_info:
            account_value = account_info.get('NetLiquidation', 0)
            summary['account_value'] = account_value
            summary['daily_risk_percent'] = (abs(self.daily_pnl) / account_value) * 100 if account_value > 0 else 0
        
        if positions:
            summary['open_positions'] = len(positions)
            summary['spx_positions'] = len([p for p in positions if 'SPX' in str(p)])
        
        return summary
    
    def should_stop_trading(self, account_info=None):
        """Determine if trading should be stopped for the day"""
        # Check daily loss limit
        if abs(self.daily_pnl) >= self.max_daily_loss:
            return True, "Daily loss limit reached"
        
        # Check trade count limit
        if self.trades_today >= self.max_trades_per_day:
            return True, "Daily trade limit reached"
        
        # Check account drawdown
        if account_info:
            account_value = account_info.get('NetLiquidation', 100000)
            drawdown_percent = (abs(self.daily_pnl) / account_value) * 100
            
            if drawdown_percent >= 5:  # 5% daily drawdown limit
                return True, f"Daily drawdown limit reached: {drawdown_percent:.1f}%"
        
        return False, "Trading can continue"