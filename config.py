import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    IB_HOST = os.getenv('IB_HOST', '127.0.0.1')
    IB_PORT = int(os.getenv('IB_PORT', '7497'))
    IB_CLIENT_ID = int(os.getenv('IB_CLIENT_ID', '1'))
    
    # Trading Parameters
    SPREAD_WIDTH = 10  # $10 width for credit spreads
    MIN_CREDIT = 2.0   # Minimum credit to collect
    MAX_RISK_PER_TRADE = 1000  # Maximum risk per trade
    TARGET_DELTA = 0.15  # Target delta for short strikes
    MIN_PROBABILITY = 0.70  # Minimum probability of profit
    
    # Market Analysis Parameters
    ANALYSIS_TIME = "07:00"  # 7 AM PST analysis time
    MARKET_OPEN_TIME = "06:30"  # 6:30 AM PST market open
    
    # Technical Indicator Parameters
    RSI_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BB_PERIOD = 20
    BB_STD = 2
    
    # Strategy Thresholds
    BULLISH_RSI_MIN = 40
    BULLISH_RSI_MAX = 70
    BEARISH_RSI_MIN = 30
    BEARISH_RSI_MAX = 60
    SIDEWAYS_THRESHOLD = 0.5  # VIX threshold for sideways market
    
    # Notification Settings
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')