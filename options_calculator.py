import numpy as np
import pandas as pd
from scipy.stats import norm
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega, rho
from datetime import datetime, timedelta
import yfinance as yf
from config import Config

class OptionsCalculator:
    def __init__(self):
        self.config = Config()
        self.risk_free_rate = 0.05  # Default 5% risk-free rate
        
    def get_risk_free_rate(self):
        """Get current risk-free rate from 10-year Treasury"""
        try:
            treasury = yf.Ticker("^TNX")
            data = treasury.history(period="5d")
            if not data.empty:
                self.risk_free_rate = data['Close'].iloc[-1] / 100
            return self.risk_free_rate
        except:
            return self.risk_free_rate
    
    def calculate_implied_volatility(self, spot_price, strike, time_to_expiry, option_price, option_type='call'):
        """Calculate implied volatility using Newton-Raphson method"""
        try:
            # Initial guess for volatility
            vol = 0.2
            tolerance = 1e-6
            max_iterations = 100
            
            for i in range(max_iterations):
                # Calculate option price and vega
                calculated_price = black_scholes(
                    option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, vol
                )
                
                option_vega = vega(
                    option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, vol
                )
                
                # Newton-Raphson update
                price_diff = calculated_price - option_price
                
                if abs(price_diff) < tolerance:
                    return vol
                    
                if option_vega == 0:
                    break
                    
                vol = vol - price_diff / option_vega
                
                # Keep volatility positive
                vol = max(vol, 0.01)
                
            return vol
        except:
            return 0.2  # Default volatility if calculation fails
    
    def calculate_option_price(self, spot_price, strike, time_to_expiry, volatility, option_type='call'):
        """Calculate option price using Black-Scholes"""
        try:
            return black_scholes(
                option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility
            )
        except:
            return 0
    
    def calculate_greeks(self, spot_price, strike, time_to_expiry, volatility, option_type='call'):
        """Calculate option Greeks"""
        try:
            greeks = {
                'delta': delta(option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility),
                'gamma': gamma(option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility),
                'theta': theta(option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility),
                'vega': vega(option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility),
                'rho': rho(option_type, spot_price, strike, time_to_expiry, self.risk_free_rate, volatility)
            }
            return greeks
        except:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    def calculate_time_to_expiry(self, expiry_date):
        """Calculate time to expiry in years"""
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        
        now = datetime.now()
        time_diff = expiry_date - now
        return max(time_diff.total_seconds() / (365.25 * 24 * 3600), 1/365.25)  # Minimum 1 day
    
    def find_strike_by_delta(self, spot_price, target_delta, time_to_expiry, volatility, option_type='put'):
        """Find strike price for a target delta"""
        try:
            # Binary search for strike
            low_strike = spot_price * 0.5
            high_strike = spot_price * 1.5
            tolerance = 0.01
            
            for _ in range(50):  # Max iterations
                mid_strike = (low_strike + high_strike) / 2
                
                calculated_delta = delta(
                    option_type, spot_price, mid_strike, time_to_expiry, self.risk_free_rate, volatility
                )
                
                if abs(calculated_delta - target_delta) < tolerance:
                    return mid_strike
                
                if option_type == 'put':
                    if calculated_delta > target_delta:  # Delta too high (less negative)
                        low_strike = mid_strike
                    else:
                        high_strike = mid_strike
                else:  # call
                    if calculated_delta > target_delta:
                        high_strike = mid_strike
                    else:
                        low_strike = mid_strike
            
            return mid_strike
        except:
            return spot_price
    
    def calculate_probability_of_profit(self, spot_price, short_strike, long_strike, 
                                      time_to_expiry, volatility, strategy_type='put_credit_spread'):
        """Calculate probability of profit for different strategies"""
        try:
            if strategy_type == 'put_credit_spread':
                # For put credit spread, profit if price stays above short strike
                # Using normal distribution assumption
                drift = self.risk_free_rate - 0.5 * volatility**2
                final_price_mean = spot_price * np.exp(drift * time_to_expiry)
                final_price_std = spot_price * volatility * np.sqrt(time_to_expiry)
                
                # Probability that final price > short strike
                z_score = (short_strike - final_price_mean) / final_price_std
                prob_profit = 1 - norm.cdf(z_score)
                
                return prob_profit
            
            elif strategy_type == 'call_diagonal':
                # For call diagonal, more complex calculation needed
                # Simplified: probability that short call expires OTM
                drift = self.risk_free_rate - 0.5 * volatility**2
                final_price_mean = spot_price * np.exp(drift * time_to_expiry)
                final_price_std = spot_price * volatility * np.sqrt(time_to_expiry)
                
                z_score = (short_strike - final_price_mean) / final_price_std
                prob_profit = norm.cdf(z_score)
                
                return prob_profit
                
        except:
            return 0.5  # Default 50% if calculation fails
    
    def calculate_spread_metrics(self, spot_price, short_strike, long_strike, 
                               time_to_expiry, volatility, option_type='put'):
        """Calculate metrics for credit/debit spreads"""
        # Get risk-free rate
        self.get_risk_free_rate()
        
        # Calculate option prices
        short_price = self.calculate_option_price(
            spot_price, short_strike, time_to_expiry, volatility, option_type
        )
        long_price = self.calculate_option_price(
            spot_price, long_strike, time_to_expiry, volatility, option_type
        )
        
        # Calculate Greeks for both options
        short_greeks = self.calculate_greeks(
            spot_price, short_strike, time_to_expiry, volatility, option_type
        )
        long_greeks = self.calculate_greeks(
            spot_price, long_strike, time_to_expiry, volatility, option_type
        )
        
        # Spread metrics
        if option_type == 'put' and short_strike > long_strike:
            # Put credit spread
            credit = short_price - long_price
            max_profit = credit
            max_loss = (short_strike - long_strike) - credit
            breakeven = short_strike - credit
            
        elif option_type == 'call' and short_strike < long_strike:
            # Call credit spread
            credit = short_price - long_price
            max_profit = credit
            max_loss = (long_strike - short_strike) - credit
            breakeven = short_strike + credit
            
        else:
            # Debit spread
            debit = long_price - short_price
            max_profit = (abs(long_strike - short_strike)) - debit
            max_loss = debit
            breakeven = min(short_strike, long_strike) + debit if option_type == 'call' else max(short_strike, long_strike) - debit
        
        # Net Greeks
        net_delta = short_greeks['delta'] - long_greeks['delta']
        net_gamma = short_greeks['gamma'] - long_greeks['gamma']
        net_theta = short_greeks['theta'] - long_greeks['theta']
        net_vega = short_greeks['vega'] - long_greeks['vega']
        
        return {
            'short_price': short_price,
            'long_price': long_price,
            'net_credit': short_price - long_price,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'profit_loss_ratio': max_profit / max_loss if max_loss > 0 else 0,
            'net_delta': net_delta,
            'net_gamma': net_gamma,
            'net_theta': net_theta,
            'net_vega': net_vega,
            'short_greeks': short_greeks,
            'long_greeks': long_greeks
        }