import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import pytz
from config import Config

class MarketAnalyzer:
    def __init__(self):
        self.config = Config()
        self.spx_ticker = "^SPX"
        self.vix_ticker = "^VIX"
        
    def get_market_data(self, days_back=30):
        """Fetch SPX and VIX data for analysis"""
        try:
            # Get SPX data
            spx = yf.Ticker(self.spx_ticker)
            spx_data = spx.history(period=f"{days_back}d", interval="1h")
            
            # Get VIX data
            vix = yf.Ticker(self.vix_ticker)
            vix_data = vix.history(period=f"{days_back}d", interval="1h")
            
            return spx_data, vix_data
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None, None
    
    def calculate_technical_indicators(self, data):
        """Calculate technical indicators for market analysis"""
        if data is None or data.empty:
            return None
            
        indicators = {}
        
        # RSI
        indicators['rsi'] = ta.momentum.RSIIndicator(
            data['Close'], window=self.config.RSI_PERIOD
        ).rsi()
        
        # MACD
        macd = ta.trend.MACD(
            data['Close'], 
            window_fast=self.config.MACD_FAST,
            window_slow=self.config.MACD_SLOW,
            window_sign=self.config.MACD_SIGNAL
        )
        indicators['macd'] = macd.macd()
        indicators['macd_signal'] = macd.macd_signal()
        indicators['macd_histogram'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(
            data['Close'], 
            window=self.config.BB_PERIOD,
            window_dev=self.config.BB_STD
        )
        indicators['bb_upper'] = bb.bollinger_hband()
        indicators['bb_middle'] = bb.bollinger_mavg()
        indicators['bb_lower'] = bb.bollinger_lband()
        indicators['bb_width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        
        # Moving Averages
        indicators['sma_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
        indicators['sma_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
        indicators['ema_12'] = ta.trend.EMAIndicator(data['Close'], window=12).ema_indicator()
        indicators['ema_26'] = ta.trend.EMAIndicator(data['Close'], window=26).ema_indicator()
        
        # Volume indicators
        indicators['volume_sma'] = ta.volume.VolumeSMAIndicator(
            data['Close'], data['Volume'], window=20
        ).volume_sma()
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(
            data['High'], data['Low'], data['Close']
        )
        indicators['stoch_k'] = stoch.stoch()
        indicators['stoch_d'] = stoch.stoch_signal()
        
        return indicators
    
    def analyze_market_direction(self, spx_data, vix_data):
        """Analyze market direction based on technical indicators"""
        if spx_data is None or vix_data is None:
            return "UNKNOWN"
            
        # Calculate indicators
        indicators = self.calculate_technical_indicators(spx_data)
        if indicators is None:
            return "UNKNOWN"
            
        # Get latest values
        latest_idx = -1
        current_price = spx_data['Close'].iloc[latest_idx]
        current_rsi = indicators['rsi'].iloc[latest_idx]
        current_macd = indicators['macd'].iloc[latest_idx]
        current_macd_signal = indicators['macd_signal'].iloc[latest_idx]
        current_bb_position = (current_price - indicators['bb_lower'].iloc[latest_idx]) / (
            indicators['bb_upper'].iloc[latest_idx] - indicators['bb_lower'].iloc[latest_idx]
        )
        current_vix = vix_data['Close'].iloc[latest_idx]
        
        # Price relative to moving averages
        sma_20 = indicators['sma_20'].iloc[latest_idx]
        sma_50 = indicators['sma_50'].iloc[latest_idx]
        
        # Scoring system
        bullish_score = 0
        bearish_score = 0
        
        # RSI analysis
        if 40 <= current_rsi <= 70:
            bullish_score += 2
        elif current_rsi > 70:
            bearish_score += 1
        elif current_rsi < 30:
            bullish_score += 1
            
        # MACD analysis
        if current_macd > current_macd_signal:
            bullish_score += 2
        else:
            bearish_score += 1
            
        # Price vs Moving Averages
        if current_price > sma_20 > sma_50:
            bullish_score += 2
        elif current_price < sma_20 < sma_50:
            bearish_score += 2
            
        # Bollinger Bands position
        if 0.2 <= current_bb_position <= 0.8:
            bullish_score += 1
        elif current_bb_position > 0.8:
            bearish_score += 1
            
        # VIX analysis
        if current_vix < 20:
            bullish_score += 1
        elif current_vix > 30:
            bearish_score += 2
            
        # Volume analysis
        recent_volume = spx_data['Volume'].iloc[-5:].mean()
        avg_volume = indicators['volume_sma'].iloc[latest_idx]
        if recent_volume > avg_volume * 1.2:
            if bullish_score > bearish_score:
                bullish_score += 1
            else:
                bearish_score += 1
                
        # Determine market direction
        if bullish_score >= bearish_score + 2:
            return "BULLISH"
        elif bearish_score >= bullish_score + 2:
            return "BEARISH"
        else:
            return "SIDEWAYS"
    
    def get_market_analysis(self):
        """Get comprehensive market analysis"""
        spx_data, vix_data = self.get_market_data()
        
        if spx_data is None or vix_data is None:
            return None
            
        direction = self.analyze_market_direction(spx_data, vix_data)
        indicators = self.calculate_technical_indicators(spx_data)
        
        current_price = spx_data['Close'].iloc[-1]
        current_vix = vix_data['Close'].iloc[-1]
        
        analysis = {
            'timestamp': datetime.now(pytz.timezone('US/Pacific')),
            'direction': direction,
            'spx_price': current_price,
            'vix_level': current_vix,
            'rsi': indicators['rsi'].iloc[-1] if indicators else None,
            'macd': indicators['macd'].iloc[-1] if indicators else None,
            'bb_position': None,
            'volume_ratio': None
        }
        
        if indicators:
            # Bollinger Band position
            bb_upper = indicators['bb_upper'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            analysis['bb_position'] = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            # Volume ratio
            recent_volume = spx_data['Volume'].iloc[-5:].mean()
            avg_volume = indicators['volume_sma'].iloc[-1]
            analysis['volume_ratio'] = recent_volume / avg_volume if avg_volume > 0 else 1
            
        return analysis