# SPX 0DTE Trading Bot 🤖📈

A sophisticated Python trading bot for 0 DTE (Days to Expiration) SPX options trading. The bot analyzes market conditions at 7 AM PST daily and executes high-probability trades based on technical analysis.

## 🌟 Features

### 📊 Market Analysis
- **Real-time SPX data** using Yahoo Finance
- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands, Stochastic
- **VIX analysis** for volatility assessment
- **Volume analysis** and market breadth indicators
- **Pre-market sentiment** evaluation

### 🎯 Trading Strategies
1. **Put Credit Spreads** (Bullish Markets)
   - $10 wide spreads
   - High probability of profit (>70%)
   - Target delta around 0.15
   - Automatic strike selection based on support levels

2. **Call Diagonal Spreads** (Sideways Markets)
   - Front-month 0DTE short calls
   - Back-month long calls for protection
   - Favorable volatility skew optimization
   - Time decay advantage

### 🛡️ Risk Management
- **Position sizing** based on account value (2% risk per trade)
- **Daily loss limits** and trade count restrictions
- **Greeks validation** (Delta, Theta, Vega limits)
- **Market condition filters** (VIX, RSI thresholds)
- **Concentration risk** controls

### 🔗 Broker Integration
- **Interactive Brokers** API support
- **Paper trading mode** for testing
- **Real-time market data** and order execution
- **Position monitoring** and management

### 📱 Notifications
- **Email notifications** (Gmail, custom SMTP)
- **Telegram alerts** with formatted messages
- **Slack integration** for team notifications
- **Daily summaries** and trade confirmations

### ⏰ Automation
- **Scheduled execution** at 7 AM PST
- **Market hours validation**
- **Weekend/holiday detection**
- **Automatic error handling** and recovery

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Interactive Brokers account (for live trading)
- TWS or IB Gateway running (for live trading)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd spx-0dte-trading-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create environment configuration**
```bash
python main_trading_bot.py --create-env
cp .env.template .env
```

4. **Configure your settings** in `.env`:
```env
# Interactive Brokers Settings
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

# Email Notifications
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL=your-email@gmail.com

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Slack Notifications (optional)
SLACK_WEBHOOK_URL=your-webhook-url
```

### Usage

#### 🧪 Test Mode (Recommended First)
```bash
# Run a single analysis in paper trading mode
python main_trading_bot.py --mode manual

# Test with notifications disabled
python main_trading_bot.py --mode manual --no-notifications
```

#### ⏰ Scheduled Mode
```bash
# Start the bot with daily 7 AM PST execution (paper trading)
python main_trading_bot.py --mode scheduled

# Run with live trading (CAUTION: Real money!)
python main_trading_bot.py --mode scheduled --live
```

#### 📊 Manual Analysis
```bash
# Run immediate market analysis and trading
python main_trading_bot.py --mode manual
```

## 📁 Project Structure

```
spx-0dte-trading-bot/
├── main_trading_bot.py      # Main entry point
├── config.py                # Configuration settings
├── market_analyzer.py       # Market analysis and indicators
├── strategy_engine.py       # Trading strategy logic
├── options_calculator.py    # Options pricing and Greeks
├── trading_interface.py     # Broker API integration
├── risk_management.py       # Risk controls and validation
├── scheduler.py             # Automated scheduling
├── notifications.py         # Alert system
├── requirements.txt         # Python dependencies
├── .env.template           # Environment template
└── logs/                   # Trading logs
```

## 🔧 Configuration

### Trading Parameters

Edit `config.py` to customize:

```python
# Trading Parameters
SPREAD_WIDTH = 10           # $10 width for credit spreads
MIN_CREDIT = 2.0           # Minimum credit to collect
MAX_RISK_PER_TRADE = 1000  # Maximum risk per trade
TARGET_DELTA = 0.15        # Target delta for short strikes
MIN_PROBABILITY = 0.70     # Minimum probability of profit

# Technical Indicator Parameters
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
BB_PERIOD = 20

# Strategy Thresholds
BULLISH_RSI_MIN = 40
BULLISH_RSI_MAX = 70
```

### Risk Management

```python
# Risk Parameters (in risk_management.py)
max_daily_loss = 5000       # Maximum daily loss
max_position_size = 10      # Maximum contracts per position
max_trades_per_day = 5      # Daily trade limit
```

## 📊 Market Analysis Logic

### Bullish Signals
- RSI between 40-70
- MACD above signal line
- Price above 20 & 50 SMA
- VIX < 20
- Strong volume confirmation

### Sideways/Choppy Signals
- RSI between 30-70
- Price within Bollinger Bands
- Low volatility environment
- Conflicting indicators

### Bearish Signals
- RSI < 30 or > 70
- MACD below signal line
- Price below moving averages
- VIX > 30
- High volatility

## 🎯 Trading Strategies Explained

### Put Credit Spreads
**When**: Bullish market conditions
**Structure**: 
- Sell higher strike put (short)
- Buy lower strike put (long)
- Collect net credit upfront

**Example**:
- SPX at 4500
- Sell 4450 Put, Buy 4440 Put
- Collect $3.50 credit
- Max profit: $3.50
- Max loss: $6.50
- Breakeven: 4446.50

### Call Diagonal Spreads
**When**: Sideways/neutral market conditions
**Structure**: 
- Sell near-term call (0DTE)
- Buy longer-term call (1 week)
- Benefit from time decay

**Example**:
- SPX at 4500
- Sell 4520 Call (0DTE)
- Buy 4540 Call (7DTE)
- Collect time decay while protected

## 📈 Performance Tracking

The bot logs all activities and provides:

- **Daily P&L tracking**
- **Win/loss ratios**
- **Risk metrics**
- **Trade performance analytics**
- **Market condition correlation**

Logs are stored in `logs/trading_bot_YYYYMMDD.log`

## 🔔 Notifications Setup

### Email Setup (Gmail)
1. Enable 2-factor authentication
2. Generate app password
3. Use app password in `.env` file

### Telegram Setup
1. Create bot with @BotFather
2. Get bot token
3. Find your chat ID
4. Configure in `.env`

### Slack Setup
1. Create incoming webhook
2. Configure webhook URL
3. Add to `.env`

## ⚠️ Risk Warnings

**IMPORTANT**: This bot trades real money when in live mode. Please:

1. **Start with paper trading** to test the system
2. **Use small position sizes** initially
3. **Monitor the bot regularly**
4. **Understand the strategies** before deploying
5. **Have stop-loss procedures** in place
6. **Keep adequate account funding**

### Risk Factors
- **0DTE options** are highly volatile and can expire worthless
- **Market gaps** can cause significant losses
- **System failures** could prevent trade management
- **Broker connectivity** issues may affect execution

## 🛠️ Deployment Options

### Local Machine
```bash
# Run on your computer
python main_trading_bot.py --mode scheduled
```

### Cloud Deployment (AWS/GCP)
1. Set up virtual machine
2. Install dependencies
3. Configure cron job for 7 AM PST
4. Set up monitoring and alerts

### Docker Container
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main_trading_bot.py", "--mode", "scheduled"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Market data errors**
   - Check internet connection
   - Verify Yahoo Finance access
   - Try different data sources

2. **Broker connection issues**
   - Ensure TWS/IB Gateway is running
   - Check port and client ID
   - Verify account permissions

3. **Notification failures**
   - Check API keys and tokens
   - Verify network connectivity
   - Test notification services separately

### Debug Mode
```bash
# Enable verbose logging
python main_trading_bot.py --mode manual --debug
```

## 📚 Advanced Features

### Backtesting
```python
# Custom backtesting module (future enhancement)
from backtester import BacktestEngine
backtester = BacktestEngine()
results = backtester.run(start_date, end_date)
```

### Custom Strategies
Extend the `StrategyEngine` class to add new strategies:

```python
def find_iron_condor(self, market_analysis):
    # Custom iron condor implementation
    pass
```

### API Integration
Add new data sources by extending `MarketAnalyzer`:

```python
def get_alternative_data(self):
    # Integration with other data providers
    pass
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

This project is for educational purposes. Use at your own risk.

## 📞 Support

For questions or issues:
1. Check the logs first
2. Review configuration settings
3. Test in paper trading mode
4. Create GitHub issue with details

## 🎯 Roadmap

- [ ] Additional strategy types (Iron Condors, Strangles)
- [ ] Machine learning market prediction
- [ ] Advanced backtesting framework
- [ ] Web dashboard for monitoring
- [ ] Mobile app notifications
- [ ] Multi-timeframe analysis
- [ ] Earnings calendar integration
- [ ] Social sentiment analysis

---

**Disclaimer**: This software is for educational and research purposes only. Trading options involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.
