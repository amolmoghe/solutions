#!/usr/bin/env python3
"""
SPX 0DTE Trading Bot
===================

A comprehensive trading bot for 0 DTE (Days to Expiration) SPX options.
Analyzes market conditions at 7 AM PST and executes:
- Put Credit Spreads for bullish markets
- Call Diagonal Spreads for sideways markets

Features:
- Real-time market analysis with technical indicators
- Risk management and position sizing
- Interactive Brokers integration
- Email/Telegram/Slack notifications
- Comprehensive logging
- Paper trading mode for testing

Author: AI Trading Bot
Version: 1.0
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
import pytz
import logging

# Import our modules
from market_analyzer import MarketAnalyzer
from strategy_engine import StrategyEngine
from trading_interface import TradingInterface, PaperTradingInterface
from risk_management import RiskManager
from scheduler import TradingScheduler
from notifications import NotificationManager
from config import Config

class SPXTradingBot:
    def __init__(self, use_paper_trading=True, enable_notifications=True):
        self.config = Config()
        self.use_paper_trading = use_paper_trading
        self.enable_notifications = enable_notifications
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer()
        self.strategy_engine = StrategyEngine()
        self.risk_manager = RiskManager()
        self.notification_manager = NotificationManager() if enable_notifications else None
        
        # Choose trading interface
        if use_paper_trading:
            self.trading_interface = PaperTradingInterface()
        else:
            self.trading_interface = TradingInterface()
        
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Set up comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Suppress some noisy loggers
        logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
        logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)
    
    async def analyze_market(self):
        """
        Analyze market conditions using technical indicators
        Returns market analysis dict or None if analysis fails
        """
        try:
            self.logger.info("Starting market analysis...")
            
            # Get comprehensive market analysis
            market_analysis = self.market_analyzer.get_market_analysis()
            
            if market_analysis is None:
                self.logger.error("Failed to get market analysis")
                if self.notification_manager:
                    self.notification_manager.send_error_notification(
                        "Failed to get market analysis", 
                        "Market data retrieval failed"
                    )
                return None
            
            # Log analysis results
            self.logger.info("=== MARKET ANALYSIS RESULTS ===")
            self.logger.info(f"Timestamp: {market_analysis['timestamp']}")
            self.logger.info(f"Direction: {market_analysis['direction']}")
            self.logger.info(f"SPX Price: ${market_analysis['spx_price']:.2f}")
            self.logger.info(f"VIX Level: {market_analysis['vix_level']:.1f}")
            self.logger.info(f"RSI: {market_analysis['rsi']:.1f}")
            self.logger.info(f"BB Position: {market_analysis.get('bb_position', 0):.2f}")
            self.logger.info(f"Volume Ratio: {market_analysis.get('volume_ratio', 1):.2f}")
            
            # Send notification
            if self.notification_manager:
                self.notification_manager.send_market_analysis_notification(market_analysis)
            
            return market_analysis
            
        except Exception as e:
            error_msg = f"Error in market analysis: {str(e)}"
            self.logger.error(error_msg)
            if self.notification_manager:
                self.notification_manager.send_error_notification(error_msg, "analyze_market()")
            return None
    
    def decide_trade_type(self, market_analysis):
        """
        Decide trade type based on market analysis
        Returns list of trade recommendations
        """
        try:
            if market_analysis is None:
                return []
            
            self.logger.info("Generating trade recommendations...")
            
            # Generate recommendations based on market direction
            recommendations = self.strategy_engine.generate_trade_recommendations(market_analysis)
            
            if not recommendations:
                self.logger.info("No suitable trades found for current market conditions")
                return []
            
            # Log recommendations
            self.logger.info(f"Generated {len(recommendations)} trade recommendation(s)")
            for i, trade in enumerate(recommendations, 1):
                self.logger.info(f"Trade {i}: {trade['strategy']} - {trade['recommendation']}")
            
            return recommendations
            
        except Exception as e:
            error_msg = f"Error in trade decision: {str(e)}"
            self.logger.error(error_msg)
            if self.notification_manager:
                self.notification_manager.send_error_notification(error_msg, "decide_trade_type()")
            return []
    
    def generate_trade_structure(self, recommendations):
        """
        Generate detailed trade structures for recommendations
        Returns validated trade structures
        """
        try:
            validated_trades = []
            
            for trade in recommendations:
                # Format trade summary
                trade_summary = self.strategy_engine.format_trade_summary(trade)
                self.logger.info(f"Trade Structure:\n{trade_summary}")
                
                # Validate trade with risk management
                account_info = None
                try:
                    account_info = asyncio.run(self.trading_interface.get_account_info())
                except:
                    self.logger.warning("Could not get account info for validation")
                
                validation = self.risk_manager.validate_trade(trade, account_info)
                
                if validation['approved']:
                    trade['validation'] = validation
                    validated_trades.append(trade)
                    self.logger.info(f"Trade approved: {trade['strategy']}")
                    
                    if validation['warnings']:
                        self.logger.warning(f"Trade warnings: {', '.join(validation['warnings'])}")
                else:
                    self.logger.warning(f"Trade rejected: {', '.join(validation['reasons'])}")
            
            return validated_trades
            
        except Exception as e:
            error_msg = f"Error generating trade structure: {str(e)}"
            self.logger.error(error_msg)
            if self.notification_manager:
                self.notification_manager.send_error_notification(error_msg, "generate_trade_structure()")
            return []
    
    async def place_trade(self, validated_trades):
        """
        Place validated trades through the trading interface
        Returns list of executed trades
        """
        executed_trades = []
        
        try:
            # Connect to trading interface
            if not await self.trading_interface.connect():
                self.logger.error("Failed to connect to trading interface")
                return executed_trades
            
            for trade in validated_trades:
                try:
                    # Check if we should stop trading
                    account_info = await self.trading_interface.get_account_info()
                    should_stop, reason = self.risk_manager.should_stop_trading(account_info)
                    
                    if should_stop:
                        self.logger.warning(f"Stopping trading: {reason}")
                        break
                    
                    # Send trade notification
                    if self.notification_manager:
                        action = "EXECUTING" if trade['recommendation'] == 'EXECUTE' else "MONITORING"
                        self.notification_manager.send_trade_notification(trade, action)
                    
                    # Execute trade if recommended
                    if trade['recommendation'] == 'EXECUTE':
                        success = await self.trading_interface.execute_trade(trade)
                        
                        if success:
                            executed_trades.append(trade)
                            self.risk_manager.update_daily_metrics(new_trade=True)
                            self.logger.info(f"✅ Trade executed: {trade['strategy']}")
                            
                            # Send execution confirmation
                            if self.notification_manager:
                                self.notification_manager.send_trade_notification(trade, "EXECUTED")
                        else:
                            self.logger.error(f"❌ Failed to execute trade: {trade['strategy']}")
                    else:
                        self.logger.info(f"📊 Trade marked for monitoring: {trade['strategy']}")
                
                except Exception as e:
                    self.logger.error(f"Error executing individual trade: {e}")
            
            return executed_trades
            
        except Exception as e:
            error_msg = f"Error in trade execution: {str(e)}"
            self.logger.error(error_msg)
            if self.notification_manager:
                self.notification_manager.send_error_notification(error_msg, "place_trade()")
            return executed_trades
        
        finally:
            self.trading_interface.disconnect()
    
    def log_and_notify(self, executed_trades, market_analysis):
        """
        Log trading session results and send notifications
        """
        try:
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Log session summary
            self.logger.info("=== TRADING SESSION SUMMARY ===")
            self.logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
            self.logger.info(f"Market Direction: {market_analysis.get('direction', 'UNKNOWN') if market_analysis else 'UNKNOWN'}")
            self.logger.info(f"Trades Executed: {len(executed_trades)}")
            self.logger.info(f"Daily P&L: ${risk_summary['daily_pnl']:.2f}")
            
            # Log individual trades
            for i, trade in enumerate(executed_trades, 1):
                self.logger.info(f"Trade {i}: {trade['strategy']} - "
                               f"Credit/Debit: ${trade.get('net_credit', trade.get('net_debit', 0)):.2f} - "
                               f"P(Profit): {trade['prob_profit']:.1%}")
            
            # Send daily summary notification
            if self.notification_manager:
                self.notification_manager.send_daily_summary(executed_trades, risk_summary)
            
        except Exception as e:
            self.logger.error(f"Error in logging and notification: {e}")
    
    async def run_daily_analysis(self):
        """
        Run the complete daily analysis and trading workflow
        """
        self.logger.info("🚀 Starting SPX 0DTE Trading Bot Daily Analysis")
        self.logger.info(f"Mode: {'Paper Trading' if self.use_paper_trading else 'Live Trading'}")
        
        try:
            # Step 1: Analyze Market
            market_analysis = await self.analyze_market()
            if market_analysis is None:
                self.logger.error("Cannot proceed without market analysis")
                return
            
            # Step 2: Decide Trade Type
            recommendations = self.decide_trade_type(market_analysis)
            if not recommendations:
                self.logger.info("No trades recommended for today")
                self.log_and_notify([], market_analysis)
                return
            
            # Step 3: Generate Trade Structure
            validated_trades = self.generate_trade_structure(recommendations)
            if not validated_trades:
                self.logger.info("No trades passed validation")
                self.log_and_notify([], market_analysis)
                return
            
            # Step 4: Place Trades
            executed_trades = await self.place_trade(validated_trades)
            
            # Step 5: Log and Notify
            self.log_and_notify(executed_trades, market_analysis)
            
            self.logger.info("✅ Daily analysis completed successfully")
            
        except Exception as e:
            error_msg = f"Critical error in daily analysis: {str(e)}"
            self.logger.error(error_msg)
            if self.notification_manager:
                self.notification_manager.send_error_notification(error_msg, "run_daily_analysis()")
    
    def start_scheduled_bot(self):
        """Start the bot with scheduled execution"""
        scheduler = TradingScheduler(self.use_paper_trading)
        scheduler.notification_manager = self.notification_manager
        scheduler.start_bot()

def create_env_template():
    """Create a template .env file"""
    env_template = """# SPX Trading Bot Configuration
# Copy this to .env and fill in your values

# Interactive Brokers Settings
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

# Email Notifications
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL=your-email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Slack Notifications
SLACK_WEBHOOK_URL=your-webhook-url

# API Keys (Optional)
ALPHA_VANTAGE_API_KEY=your-api-key
POLYGON_API_KEY=your-api-key
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("Created .env.template file. Copy to .env and configure your settings.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='SPX 0DTE Trading Bot')
    parser.add_argument('--mode', choices=['scheduled', 'manual', 'test'], default='scheduled',
                       help='Bot execution mode')
    parser.add_argument('--live', action='store_true', 
                       help='Use live trading (default is paper trading)')
    parser.add_argument('--no-notifications', action='store_true',
                       help='Disable notifications')
    parser.add_argument('--create-env', action='store_true',
                       help='Create environment template file')
    
    args = parser.parse_args()
    
    if args.create_env:
        create_env_template()
        return
    
    # Initialize bot
    bot = SPXTradingBot(
        use_paper_trading=not args.live,
        enable_notifications=not args.no_notifications
    )
    
    if args.mode == 'scheduled':
        print("Starting scheduled trading bot...")
        print("Bot will run daily at 7 AM PST")
        print("Press Ctrl+C to stop")
        bot.start_scheduled_bot()
        
    elif args.mode == 'manual':
        print("Running manual analysis...")
        asyncio.run(bot.run_daily_analysis())
        
    elif args.mode == 'test':
        print("Running test mode...")
        # Run a quick test of all components
        asyncio.run(bot.run_daily_analysis())

if __name__ == "__main__":
    main()