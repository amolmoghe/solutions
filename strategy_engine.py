import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from options_calculator import OptionsCalculator
from market_analyzer import MarketAnalyzer
from config import Config

class StrategyEngine:
    def __init__(self):
        self.config = Config()
        self.options_calc = OptionsCalculator()
        self.market_analyzer = MarketAnalyzer()
        
    def get_0dte_expiry(self):
        """Get today's date as 0DTE expiry"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def estimate_volatility(self, spx_data, vix_level):
        """Estimate volatility for options pricing"""
        try:
            # Use VIX as primary volatility estimate
            implied_vol = vix_level / 100
            
            # Also calculate historical volatility as backup
            if spx_data is not None and len(spx_data) > 20:
                returns = np.log(spx_data['Close'] / spx_data['Close'].shift(1))
                hist_vol = returns.std() * np.sqrt(252)  # Annualized
                
                # Blend VIX and historical volatility
                volatility = 0.7 * implied_vol + 0.3 * hist_vol
            else:
                volatility = implied_vol
                
            return max(volatility, 0.1)  # Minimum 10% volatility
        except:
            return 0.2  # Default 20% volatility
    
    def find_put_credit_spread(self, market_analysis):
        """Find optimal put credit spread for bullish market"""
        if market_analysis is None:
            return None
            
        spot_price = market_analysis['spx_price']
        vix_level = market_analysis['vix_level']
        
        # Get market data for volatility calculation
        spx_data, _ = self.market_analyzer.get_market_data(30)
        volatility = self.estimate_volatility(spx_data, vix_level)
        
        # 0DTE expiry
        expiry_date = self.get_0dte_expiry()
        time_to_expiry = self.options_calc.calculate_time_to_expiry(expiry_date)
        
        # Find short strike based on target delta
        target_delta = -self.config.TARGET_DELTA  # Negative for puts
        short_strike = self.options_calc.find_strike_by_delta(
            spot_price, target_delta, time_to_expiry, volatility, 'put'
        )
        
        # Long strike is $10 below short strike
        long_strike = short_strike - self.config.SPREAD_WIDTH
        
        # Calculate spread metrics
        spread_metrics = self.options_calc.calculate_spread_metrics(
            spot_price, short_strike, long_strike, time_to_expiry, volatility, 'put'
        )
        
        # Calculate probability of profit
        prob_profit = self.options_calc.calculate_probability_of_profit(
            spot_price, short_strike, long_strike, time_to_expiry, volatility, 'put_credit_spread'
        )
        
        # Check if trade meets criteria
        if (spread_metrics['net_credit'] >= self.config.MIN_CREDIT and 
            prob_profit >= self.config.MIN_PROBABILITY and
            spread_metrics['max_loss'] <= self.config.MAX_RISK_PER_TRADE):
            
            trade = {
                'strategy': 'put_credit_spread',
                'expiry': expiry_date,
                'spot_price': spot_price,
                'short_strike': short_strike,
                'long_strike': long_strike,
                'short_delta': spread_metrics['short_greeks']['delta'],
                'net_credit': spread_metrics['net_credit'],
                'max_profit': spread_metrics['max_profit'],
                'max_loss': spread_metrics['max_loss'],
                'breakeven': spread_metrics['breakeven'],
                'prob_profit': prob_profit,
                'net_theta': spread_metrics['net_theta'],
                'net_delta': spread_metrics['net_delta'],
                'volatility_used': volatility,
                'market_direction': market_analysis['direction'],
                'vix_level': vix_level,
                'rsi': market_analysis['rsi'],
                'recommendation': 'EXECUTE' if prob_profit >= 0.75 else 'MONITOR'
            }
            
            return trade
        
        return None
    
    def find_call_diagonal(self, market_analysis):
        """Find optimal call diagonal for sideways/choppy market"""
        if market_analysis is None:
            return None
            
        spot_price = market_analysis['spx_price']
        vix_level = market_analysis['vix_level']
        
        # Get market data for volatility calculation
        spx_data, _ = self.market_analyzer.get_market_data(30)
        volatility = self.estimate_volatility(spx_data, vix_level)
        
        # Short leg: 0DTE
        short_expiry = self.get_0dte_expiry()
        short_tte = self.options_calc.calculate_time_to_expiry(short_expiry)
        
        # Long leg: Next week (7 days out)
        long_expiry_date = datetime.now() + timedelta(days=7)
        long_expiry = long_expiry_date.strftime("%Y-%m-%d")
        long_tte = self.options_calc.calculate_time_to_expiry(long_expiry)
        
        # Find strikes - short call slightly OTM, long call further OTM
        short_strike = self.options_calc.find_strike_by_delta(
            spot_price, 0.25, short_tte, volatility, 'call'  # 25 delta short call
        )
        long_strike = short_strike + 20  # $20 wider than typical spread
        
        # Calculate option prices separately
        short_call_price = self.options_calc.calculate_option_price(
            spot_price, short_strike, short_tte, volatility, 'call'
        )
        long_call_price = self.options_calc.calculate_option_price(
            spot_price, long_strike, long_tte, volatility, 'call'
        )
        
        # Calculate Greeks
        short_greeks = self.options_calc.calculate_greeks(
            spot_price, short_strike, short_tte, volatility, 'call'
        )
        long_greeks = self.options_calc.calculate_greeks(
            spot_price, long_strike, long_tte, volatility, 'call'
        )
        
        # Net debit for diagonal
        net_debit = long_call_price - short_call_price
        
        # Estimate max profit (complex for diagonals, simplified here)
        max_profit = short_call_price * 0.8  # Rough estimate
        max_loss = net_debit
        
        # Probability of profit for diagonal
        prob_profit = self.options_calc.calculate_probability_of_profit(
            spot_price, short_strike, long_strike, short_tte, volatility, 'call_diagonal'
        )
        
        # Check if diagonal meets criteria
        if (net_debit <= self.config.MAX_RISK_PER_TRADE * 0.5 and  # Lower risk for diagonals
            prob_profit >= 0.6 and  # Lower prob requirement for diagonals
            short_greeks['theta'] < -0.5):  # Good theta decay
            
            trade = {
                'strategy': 'call_diagonal',
                'short_expiry': short_expiry,
                'long_expiry': long_expiry,
                'spot_price': spot_price,
                'short_strike': short_strike,
                'long_strike': long_strike,
                'short_call_price': short_call_price,
                'long_call_price': long_call_price,
                'net_debit': net_debit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'prob_profit': prob_profit,
                'short_delta': short_greeks['delta'],
                'long_delta': long_greeks['delta'],
                'net_theta': short_greeks['theta'] - long_greeks['theta'],
                'net_vega': short_greeks['vega'] - long_greeks['vega'],
                'volatility_used': volatility,
                'market_direction': market_analysis['direction'],
                'vix_level': vix_level,
                'rsi': market_analysis['rsi'],
                'recommendation': 'EXECUTE' if prob_profit >= 0.65 else 'MONITOR'
            }
            
            return trade
        
        return None
    
    def find_optimal_iron_condor(self, market_analysis):
        """Find optimal iron condor with maximum probability of success"""
        if market_analysis is None:
            return None
            
        spot_price = market_analysis['spx_price']
        vix_level = market_analysis['vix_level']
        rsi = market_analysis['rsi']
        
        # Enhanced market condition checks for Iron Condor suitability
        if not self._is_suitable_for_iron_condor(market_analysis):
            return None
        
        # Get market data for volatility calculation
        spx_data, _ = self.market_analyzer.get_market_data(30)
        volatility = self.estimate_volatility(spx_data, vix_level)
        
        # 0DTE expiry
        expiry_date = self.get_0dte_expiry()
        time_to_expiry = self.options_calc.calculate_time_to_expiry(expiry_date)
        
        # Scan multiple Iron Condor configurations for optimal setup
        best_condor = None
        best_score = 0
        
        # Test different delta configurations for maximum success (0DTE optimized)
        delta_configs = [0.05, 0.08, 0.10, 0.12, 0.15]  # More conservative deltas for 0DTE
        
        for target_delta in delta_configs:
            condor = self._build_iron_condor(
                spot_price, target_delta, time_to_expiry, volatility, market_analysis
            )
            
            if condor:
                # Score this condor configuration
                score = self._score_iron_condor(condor, market_analysis)
                
                if score > best_score:
                    best_score = score
                    best_condor = condor
                    best_condor['optimization_score'] = score
        
        # If we found a good condor, enhance it with additional analysis
        if best_condor and best_score >= 75:  # Minimum score threshold
            best_condor = self._enhance_condor_analysis(best_condor, market_analysis)
            best_condor['recommendation'] = self._determine_condor_recommendation(best_condor)
            
        return best_condor
    
    def _is_suitable_for_iron_condor(self, market_analysis):
        """Enhanced suitability check for Iron Condor strategy"""
        vix_level = market_analysis['vix_level']
        rsi = market_analysis['rsi']
        bb_position = market_analysis.get('bb_position', 0.5)
        volume_ratio = market_analysis.get('volume_ratio', 1.0)
        direction = market_analysis['direction']
        
        self.logger.info(f"Checking Iron Condor suitability:")
        self.logger.info(f"  Market Direction: {direction}")
        self.logger.info(f"  VIX Level: {vix_level:.1f}")
        self.logger.info(f"  RSI: {rsi:.1f}")
        self.logger.info(f"  BB Position: {bb_position:.2f}")
        self.logger.info(f"  Volume Ratio: {volume_ratio:.2f}")
        
        # Primary requirement: Market direction should be SIDEWAYS
        if direction != 'SIDEWAYS':
            self.logger.info(f"  ❌ Market not sideways (is {direction})")
            return False
        
        # Relaxed conditions for 0DTE Iron Condors:
        # 1. Moderate to elevated volatility (VIX 12-40) - wider range for 0DTE
        if vix_level < 12 or vix_level > 40:
            self.logger.info(f"  ❌ VIX outside optimal range (12-40): {vix_level:.1f}")
            return False
            
        # 2. RSI in neutral to slightly extended range (25-75) - more permissive
        if rsi < 25 or rsi > 75:
            self.logger.info(f"  ❌ RSI outside range (25-75): {rsi:.1f}")
            return False
            
        # 3. Price not at extreme Bollinger Band positions (0.15-0.85)
        if bb_position < 0.15 or bb_position > 0.85:
            self.logger.info(f"  ❌ BB position too extreme: {bb_position:.2f}")
            return False
            
        # 4. Volume not excessively high (suggests breakout potential)
        if volume_ratio > 2.0:  # More permissive for 0DTE
            self.logger.info(f"  ❌ Volume too high (breakout risk): {volume_ratio:.2f}")
            return False
        
        self.logger.info("  ✅ All Iron Condor suitability checks passed")
        return True
    
    def _build_iron_condor(self, spot_price, target_delta, time_to_expiry, volatility, market_analysis):
        """Build Iron Condor with specific delta configuration"""
        try:
            # Find short strikes based on target delta
            short_put_strike = self.options_calc.find_strike_by_delta(
                spot_price, -target_delta, time_to_expiry, volatility, 'put'
            )
            short_call_strike = self.options_calc.find_strike_by_delta(
                spot_price, target_delta, time_to_expiry, volatility, 'call'
            )
            
            # Long strikes with 30-point wings
            long_put_strike = short_put_strike - self.config.IRON_CONDOR_WIDTH
            long_call_strike = short_call_strike + self.config.IRON_CONDOR_WIDTH
            
            # Calculate option prices
            short_put_price = self.options_calc.calculate_option_price(
                spot_price, short_put_strike, time_to_expiry, volatility, 'put'
            )
            long_put_price = self.options_calc.calculate_option_price(
                spot_price, long_put_strike, time_to_expiry, volatility, 'put'
            )
            short_call_price = self.options_calc.calculate_option_price(
                spot_price, short_call_strike, time_to_expiry, volatility, 'call'
            )
            long_call_price = self.options_calc.calculate_option_price(
                spot_price, long_call_strike, time_to_expiry, volatility, 'call'
            )
            
            # Net credit
            net_credit = (short_put_price - long_put_price) + (short_call_price - long_call_price)
            
            # Skip if credit is too low
            if net_credit < self.config.MIN_IC_CREDIT:
                return None
            
            # Calculate Greeks
            short_put_greeks = self.options_calc.calculate_greeks(
                spot_price, short_put_strike, time_to_expiry, volatility, 'put'
            )
            short_call_greeks = self.options_calc.calculate_greeks(
                spot_price, short_call_strike, time_to_expiry, volatility, 'call'
            )
            
            # Net Greeks (simplified for key metrics)
            net_delta = short_put_greeks['delta'] + short_call_greeks['delta']
            net_theta = short_put_greeks['theta'] + short_call_greeks['theta']
            
            # Iron Condor metrics
            max_profit = net_credit
            max_loss = self.config.IRON_CONDOR_WIDTH - net_credit
            upper_breakeven = short_call_strike + net_credit
            lower_breakeven = short_put_strike - net_credit
            
            # Advanced probability calculation
            prob_profit = self._calculate_advanced_ic_probability(
                spot_price, lower_breakeven, upper_breakeven, time_to_expiry, 
                volatility, market_analysis
            )
            
            return {
                'strategy': 'iron_condor',
                'expiry': self.get_0dte_expiry(),
                'spot_price': spot_price,
                'short_put_strike': short_put_strike,
                'long_put_strike': long_put_strike,
                'short_call_strike': short_call_strike,
                'long_call_strike': long_call_strike,
                'short_put_delta': short_put_greeks['delta'],
                'short_call_delta': short_call_greeks['delta'],
                'net_credit': net_credit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'upper_breakeven': upper_breakeven,
                'lower_breakeven': lower_breakeven,
                'prob_profit': prob_profit,
                'net_delta': net_delta,
                'net_theta': net_theta,
                'target_delta': target_delta,
                'volatility_used': volatility,
                'market_direction': market_analysis['direction'],
                'vix_level': market_analysis['vix_level'],
                'rsi': market_analysis['rsi'],
                'wing_width': self.config.IRON_CONDOR_WIDTH,
                'individual_prices': {
                    'short_put': short_put_price,
                    'long_put': long_put_price,
                    'short_call': short_call_price,
                    'long_call': long_call_price
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error building iron condor: {e}")
            return None
    
    def _score_iron_condor(self, condor, market_analysis):
        """Score Iron Condor configuration for optimization (0-100 scale)"""
        score = 0
        
        # Probability of profit (40 points max)
        prob_score = min(condor['prob_profit'] * 100 * 0.4, 40)
        score += prob_score
        
        # Risk/reward ratio (20 points max)
        risk_reward = condor['max_profit'] / condor['max_loss'] if condor['max_loss'] > 0 else 0
        rr_score = min(risk_reward * 40, 20)  # Cap at 20 points
        score += rr_score
        
        # Delta neutrality (15 points max)
        delta_neutrality = max(0, 15 - abs(condor['net_delta']) * 100)
        score += delta_neutrality
        
        # Theta decay benefit (15 points max)
        theta_score = min(abs(condor['net_theta']) * 2, 15) if condor['net_theta'] > 0 else 0
        score += theta_score
        
        # Market condition alignment (10 points max)
        vix_optimal = 20 <= market_analysis['vix_level'] <= 25  # Sweet spot
        rsi_optimal = 45 <= market_analysis['rsi'] <= 55  # Neutral RSI
        
        if vix_optimal:
            score += 5
        if rsi_optimal:
            score += 5
        
        return score
    
    def _calculate_advanced_ic_probability(self, spot_price, lower_be, upper_be, 
                                         time_to_expiry, volatility, market_analysis):
        """Advanced probability calculation considering market conditions"""
        try:
            import numpy as np
            from scipy.stats import norm
            
            # Base probability using log-normal distribution
            drift = self.options_calc.risk_free_rate - 0.5 * volatility**2
            final_price_mean = spot_price * np.exp(drift * time_to_expiry)
            final_price_std = spot_price * volatility * np.sqrt(time_to_expiry)
            
            z_lower = (lower_be - final_price_mean) / final_price_std
            z_upper = (upper_be - final_price_mean) / final_price_std
            
            base_prob = norm.cdf(z_upper) - norm.cdf(z_lower)
            
            # Adjust for market conditions
            adjustment_factor = 1.0
            
            # VIX adjustment - lower VIX = higher success probability
            vix_level = market_analysis['vix_level']
            if vix_level < 20:
                adjustment_factor *= 1.1  # 10% boost for low VIX
            elif vix_level > 30:
                adjustment_factor *= 0.9  # 10% penalty for high VIX
            
            # RSI adjustment - neutral RSI is better
            rsi = market_analysis['rsi']
            if 45 <= rsi <= 55:
                adjustment_factor *= 1.05  # 5% boost for neutral RSI
            
            # Volume adjustment - high volume can indicate breakouts
            volume_ratio = market_analysis.get('volume_ratio', 1.0)
            if volume_ratio > 1.3:
                adjustment_factor *= 0.95  # Small penalty for high volume
            
            return min(base_prob * adjustment_factor, 0.95)  # Cap at 95%
            
        except Exception as e:
            self.logger.error(f"Error in advanced IC probability: {e}")
            return 0.5
    
    def _enhance_condor_analysis(self, condor, market_analysis):
        """Add enhanced analysis metrics to the condor"""
        # Calculate profit zone width
        profit_zone_width = condor['upper_breakeven'] - condor['lower_breakeven']
        profit_zone_percentage = (profit_zone_width / condor['spot_price']) * 100
        
        # Distance from current price to breakevens
        distance_to_upper_be = condor['upper_breakeven'] - condor['spot_price']
        distance_to_lower_be = condor['spot_price'] - condor['lower_breakeven']
        
        # Expected move calculation
        expected_move = condor['spot_price'] * condor['volatility_used'] * np.sqrt(condor['expiry'] if isinstance(condor['expiry'], float) else 1/365.25)
        
        condor.update({
            'profit_zone_width': profit_zone_width,
            'profit_zone_percentage': profit_zone_percentage,
            'distance_to_upper_be': distance_to_upper_be,
            'distance_to_lower_be': distance_to_lower_be,
            'expected_move': expected_move,
            'expected_move_coverage': profit_zone_width / (2 * expected_move) if expected_move > 0 else 0
        })
        
        return condor
    
    def _determine_condor_recommendation(self, condor):
        """Determine recommendation based on condor quality"""
        score = condor.get('optimization_score', 0)
        prob_profit = condor['prob_profit']
        
        if score >= 85 and prob_profit >= 0.75:
            return 'EXECUTE'
        elif score >= 75 and prob_profit >= 0.65:
            return 'EXECUTE'
        elif score >= 65:
            return 'MONITOR'
        else:
            return 'SKIP'
    
    # Keep the original method as an alias for backward compatibility
    def find_iron_condor(self, market_analysis):
        """Alias for find_optimal_iron_condor"""
        return self.find_optimal_iron_condor(market_analysis)
    
    def _calculate_ic_probability_of_profit(self, spot_price, lower_breakeven, upper_breakeven, 
                                          time_to_expiry, volatility):
        """Calculate probability that price stays between iron condor breakevens"""
        try:
            import numpy as np
            from scipy.stats import norm
            
            # Using log-normal distribution for stock prices
            drift = self.options_calc.risk_free_rate - 0.5 * volatility**2
            final_price_mean = spot_price * np.exp(drift * time_to_expiry)
            final_price_std = spot_price * volatility * np.sqrt(time_to_expiry)
            
            # Probability that final price is between breakevens
            z_lower = (lower_breakeven - final_price_mean) / final_price_std
            z_upper = (upper_breakeven - final_price_mean) / final_price_std
            
            prob_profit = norm.cdf(z_upper) - norm.cdf(z_lower)
            
            return prob_profit
            
        except Exception as e:
            self.logger.error(f"Error calculating IC probability: {e}")
            return 0.5  # Default 50% if calculation fails
    
    def generate_trade_recommendations(self, market_analysis):
        """Generate trade recommendations based on market analysis"""
        if market_analysis is None:
            return []
            
        recommendations = []
        direction = market_analysis['direction']
        
        if direction == 'BULLISH':
            # Look for put credit spreads
            put_spread = self.find_put_credit_spread(market_analysis)
            if put_spread:
                recommendations.append(put_spread)
                
        elif direction == 'SIDEWAYS':
            # PRIMARY STRATEGY: Iron Condor for sideways/range-bound/choppy markets
            self.logger.info("Market detected as SIDEWAYS - Scanning for optimal Iron Condor...")
            
            iron_condor = self.find_optimal_iron_condor(market_analysis)
            if iron_condor:
                self.logger.info(f"Iron Condor found with {iron_condor['prob_profit']:.1%} probability of profit")
                recommendations.append(iron_condor)
            else:
                self.logger.info("No suitable Iron Condor found - market conditions not optimal")
            
            # SECONDARY: Call diagonals only if Iron Condor is not suitable
            if not iron_condor:
                self.logger.info("Checking Call Diagonal as alternative to Iron Condor...")
                call_diagonal = self.find_call_diagonal(market_analysis)
                if call_diagonal:
                    recommendations.append(call_diagonal)
                
            # TERTIARY: Put credit spreads only as last resort
            if not recommendations:
                self.logger.info("Checking Put Credit Spread as backup strategy...")
                put_spread = self.find_put_credit_spread(market_analysis)
                if put_spread and put_spread['prob_profit'] >= 0.60:  # Lower threshold for backup
                    put_spread['recommendation'] = 'MONITOR'
                    recommendations.append(put_spread)
        
        elif direction == 'BEARISH':
            # For bearish markets, we might skip trades or look for different strategies
            # This could be expanded to include bear call spreads
            pass
        
        return recommendations
    
    def format_trade_summary(self, trade):
        """Format trade for display"""
        if trade['strategy'] == 'put_credit_spread':
            summary = f"""
PUT CREDIT SPREAD (0DTE)
========================
Direction: {trade['market_direction']} (Bullish Strategy)
SPX Price: ${trade['spot_price']:.2f}
VIX Level: {trade['vix_level']:.1f}
RSI: {trade['rsi']:.1f}

TRADE STRUCTURE:
- Sell Put: ${trade['short_strike']:.0f} (Δ: {trade['short_delta']:.3f})
- Buy Put:  ${trade['long_strike']:.0f}
- Width: ${trade['short_strike'] - trade['long_strike']:.0f}

FINANCIALS:
- Net Credit: ${trade['net_credit']:.2f}
- Max Profit: ${trade['max_profit']:.2f}
- Max Loss: ${trade['max_loss']:.2f}
- Breakeven: ${trade['breakeven']:.2f}
- Prob of Profit: {trade['prob_profit']:.1%}

GREEKS:
- Net Delta: {trade['net_delta']:.3f}
- Net Theta: {trade['net_theta']:.3f}

RECOMMENDATION: {trade['recommendation']}
            """
            
        elif trade['strategy'] == 'call_diagonal':
            summary = f"""
CALL DIAGONAL SPREAD
===================
Direction: {trade['market_direction']} (Sideways Strategy)
SPX Price: ${trade['spot_price']:.2f}
VIX Level: {trade['vix_level']:.1f}
RSI: {trade['rsi']:.1f}

TRADE STRUCTURE:
- Sell Call: ${trade['short_strike']:.0f} (0DTE, Δ: {trade['short_delta']:.3f})
- Buy Call:  ${trade['long_strike']:.0f} ({trade['long_expiry']})

FINANCIALS:
- Net Debit: ${trade['net_debit']:.2f}
- Max Profit: ${trade['max_profit']:.2f}
- Max Loss: ${trade['max_loss']:.2f}
- Prob of Profit: {trade['prob_profit']:.1%}

GREEKS:
- Net Theta: {trade['net_theta']:.3f}
- Net Vega: {trade['net_vega']:.3f}

RECOMMENDATION: {trade['recommendation']}
            """
            
        elif trade['strategy'] == 'iron_condor':
            summary = f"""
IRON CONDOR (0DTE)
==================
Direction: {trade['market_direction']} (Range-Bound Strategy)
SPX Price: ${trade['spot_price']:.2f}
VIX Level: {trade['vix_level']:.1f}
RSI: {trade['rsi']:.1f}

TRADE STRUCTURE:
- Short Put:  ${trade['short_put_strike']:.0f} (Δ: {trade['short_put_delta']:.3f})
- Long Put:   ${trade['long_put_strike']:.0f}
- Short Call: ${trade['short_call_strike']:.0f} (Δ: {trade['short_call_delta']:.3f})
- Long Call:  ${trade['long_call_strike']:.0f}
- Wing Width: ${trade['wing_width']:.0f} points

FINANCIALS:
- Net Credit: ${trade['net_credit']:.2f}
- Max Profit: ${trade['max_profit']:.2f}
- Max Loss: ${trade['max_loss']:.2f}
- Upper Breakeven: ${trade['upper_breakeven']:.2f}
- Lower Breakeven: ${trade['lower_breakeven']:.2f}
- Profit Range: ${trade['lower_breakeven']:.2f} - ${trade['upper_breakeven']:.2f}
- Prob of Profit: {trade['prob_profit']:.1%}

GREEKS:
- Net Delta: {trade['net_delta']:.3f} (Delta Neutral)
- Net Theta: {trade['net_theta']:.3f}
- Net Vega: {trade['net_vega']:.3f}
- Net Gamma: {trade['net_gamma']:.3f}

RECOMMENDATION: {trade['recommendation']}
            """
        
        return summary