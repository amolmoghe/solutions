import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from config import Config

class NotificationManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Email settings
        self.email_enabled = bool(self.config.__dict__.get('EMAIL_USER'))
        self.telegram_enabled = bool(self.config.__dict__.get('TELEGRAM_BOT_TOKEN'))
        self.slack_enabled = bool(self.config.__dict__.get('SLACK_WEBHOOK_URL'))
    
    def send_email(self, subject, body, to_email=None):
        """Send email notification"""
        if not self.email_enabled:
            return False
            
        try:
            from_email = getattr(self.config, 'EMAIL_USER', '')
            password = getattr(self.config, 'EMAIL_PASSWORD', '')
            smtp_server = getattr(self.config, 'SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = getattr(self.config, 'SMTP_PORT', 587)
            to_email = to_email or getattr(self.config, 'NOTIFICATION_EMAIL', from_email)
            
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_telegram(self, message):
        """Send Telegram notification"""
        if not self.telegram_enabled:
            return False
            
        try:
            bot_token = getattr(self.config, 'TELEGRAM_BOT_TOKEN', '')
            chat_id = getattr(self.config, 'TELEGRAM_CHAT_ID', '')
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                self.logger.info("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_slack(self, message):
        """Send Slack notification"""
        if not self.slack_enabled:
            return False
            
        try:
            webhook_url = getattr(self.config, 'SLACK_WEBHOOK_URL', '')
            
            payload = {
                'text': message,
                'username': 'SPX Trading Bot',
                'icon_emoji': ':chart_with_upwards_trend:'
            }
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                self.logger.info("Slack message sent successfully")
                return True
            else:
                self.logger.error(f"Failed to send Slack message: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Slack message: {e}")
            return False
    
    def send_market_analysis_notification(self, market_analysis):
        """Send market analysis notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PST")
        
        subject = f"SPX Trading Bot - Market Analysis {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
🤖 <b>SPX 0DTE Trading Bot - Market Analysis</b>
📅 {timestamp}

📊 <b>Market Conditions:</b>
• Direction: <b>{market_analysis['direction']}</b>
• SPX Price: <b>${market_analysis['spx_price']:.2f}</b>
• VIX Level: <b>{market_analysis['vix_level']:.1f}</b>
• RSI: <b>{market_analysis['rsi']:.1f}</b>
• BB Position: <b>{market_analysis.get('bb_position', 0):.2f}</b>
• Volume Ratio: <b>{market_analysis.get('volume_ratio', 1):.2f}</b>

🎯 <b>Market Outlook:</b>
{self._get_market_interpretation(market_analysis)}
        """
        
        # Send via all enabled channels
        self._send_to_all_channels(subject, message)
    
    def send_trade_notification(self, trade_data, action="RECOMMENDED"):
        """Send trade recommendation/execution notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PST")
        
        subject = f"SPX Trading Bot - Trade {action} {datetime.now().strftime('%Y-%m-%d')}"
        
        if trade_data['strategy'] == 'put_credit_spread':
            message = f"""
🤖 <b>SPX 0DTE Trading Bot - Trade {action}</b>
📅 {timestamp}

📈 <b>PUT CREDIT SPREAD (0DTE)</b>
• Strategy: <b>Bullish</b>
• SPX Price: <b>${trade_data['spot_price']:.2f}</b>

🎯 <b>Trade Structure:</b>
• Sell Put: <b>${trade_data['short_strike']:.0f}</b> (Δ: {trade_data['short_delta']:.3f})
• Buy Put: <b>${trade_data['long_strike']:.0f}</b>
• Spread Width: <b>${trade_data['short_strike'] - trade_data['long_strike']:.0f}</b>

💰 <b>Financials:</b>
• Net Credit: <b>${trade_data['net_credit']:.2f}</b>
• Max Profit: <b>${trade_data['max_profit']:.2f}</b>
• Max Loss: <b>${trade_data['max_loss']:.2f}</b>
• Breakeven: <b>${trade_data['breakeven']:.2f}</b>
• Prob of Profit: <b>{trade_data['prob_profit']:.1%}</b>

📊 <b>Greeks:</b>
• Net Delta: <b>{trade_data['net_delta']:.3f}</b>
• Net Theta: <b>{trade_data['net_theta']:.3f}</b>

⚡ <b>Recommendation: {trade_data['recommendation']}</b>
            """
        
        elif trade_data['strategy'] == 'call_diagonal':
            message = f"""
🤖 <b>SPX Trading Bot - Trade {action}</b>
📅 {timestamp}

📈 <b>CALL DIAGONAL SPREAD</b>
• Strategy: <b>Sideways/Neutral</b>
• SPX Price: <b>${trade_data['spot_price']:.2f}</b>

🎯 <b>Trade Structure:</b>
• Sell Call: <b>${trade_data['short_strike']:.0f}</b> (0DTE, Δ: {trade_data['short_delta']:.3f})
• Buy Call: <b>${trade_data['long_strike']:.0f}</b> ({trade_data['long_expiry']})

💰 <b>Financials:</b>
• Net Debit: <b>${trade_data['net_debit']:.2f}</b>
• Max Profit: <b>${trade_data['max_profit']:.2f}</b>
• Max Loss: <b>${trade_data['max_loss']:.2f}</b>
• Prob of Profit: <b>{trade_data['prob_profit']:.1%}</b>

📊 <b>Greeks:</b>
• Net Theta: <b>{trade_data['net_theta']:.3f}</b>
• Net Vega: <b>{trade_data['net_vega']:.3f}</b>

⚡ <b>Recommendation: {trade_data['recommendation']}</b>
            """
        
        # Send via all enabled channels
        self._send_to_all_channels(subject, message)
    
    def send_daily_summary(self, trades_executed, risk_summary):
        """Send end of day summary"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PST")
        
        subject = f"SPX Trading Bot - Daily Summary {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
🤖 <b>SPX 0DTE Trading Bot - Daily Summary</b>
📅 {timestamp}

📊 <b>Trading Summary:</b>
• Trades Executed: <b>{len(trades_executed)}</b>
• Daily P&L: <b>${risk_summary['daily_pnl']:.2f}</b>
• Total Trades: <b>{risk_summary['trades_today']}</b>

💼 <b>Account Summary:</b>
• Account Value: <b>${risk_summary.get('account_value', 0):.2f}</b>
• Daily Risk %: <b>{risk_summary.get('daily_risk_percent', 0):.2f}%</b>
• Open Positions: <b>{risk_summary.get('open_positions', 0)}</b>

📈 <b>Executed Trades:</b>
        """
        
        for i, trade in enumerate(trades_executed, 1):
            message += f"\n{i}. {trade['strategy'].upper().replace('_', ' ')}"
            message += f" - Credit/Debit: ${trade.get('net_credit', trade.get('net_debit', 0)):.2f}"
            message += f" - P(Profit): {trade['prob_profit']:.1%}"
        
        if not trades_executed:
            message += "\nNo trades executed today."
        
        # Send via all enabled channels
        self._send_to_all_channels(subject, message)
    
    def send_error_notification(self, error_message, context=""):
        """Send error notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PST")
        
        subject = f"SPX Trading Bot - ERROR {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
🚨 <b>SPX Trading Bot - ERROR ALERT</b>
📅 {timestamp}

❌ <b>Error Details:</b>
{error_message}

🔍 <b>Context:</b>
{context}

Please check the bot logs for more details.
        """
        
        # Send via all enabled channels
        self._send_to_all_channels(subject, message)
    
    def _get_market_interpretation(self, analysis):
        """Get human-readable market interpretation"""
        direction = analysis['direction']
        vix = analysis['vix_level']
        rsi = analysis['rsi']
        
        if direction == 'BULLISH':
            return f"Market showing bullish signals. VIX at {vix:.1f} suggests moderate volatility. RSI at {rsi:.1f} indicates momentum. Suitable for put credit spreads."
        elif direction == 'BEARISH':
            return f"Market showing bearish signals. VIX at {vix:.1f} and RSI at {rsi:.1f}. Avoiding trades or considering bear strategies."
        else:  # SIDEWAYS
            return f"Market appears sideways/choppy. VIX at {vix:.1f} suggests range-bound action. Consider diagonal spreads or neutral strategies."
    
    def _send_to_all_channels(self, subject, message):
        """Send message to all enabled notification channels"""
        # Convert HTML to plain text for email
        email_message = self._html_to_plain_text(message)
        
        if self.email_enabled:
            self.send_email(subject, email_message)
        
        if self.telegram_enabled:
            self.send_telegram(message)
        
        if self.slack_enabled:
            # Convert HTML to Slack markdown
            slack_message = self._html_to_slack_markdown(message)
            self.send_slack(slack_message)
    
    def _html_to_plain_text(self, html_text):
        """Convert HTML formatted text to plain text"""
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)
    
    def _html_to_slack_markdown(self, html_text):
        """Convert HTML to Slack markdown"""
        # Replace HTML bold tags with Slack bold
        text = html_text.replace('<b>', '*').replace('</b>', '*')
        # Remove other HTML tags
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

# Add notification settings to config
def update_config_with_notifications():
    """Add notification settings to config file"""
    notification_config = """
    
    # Notification Settings
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    """
    
    # This would be added to config.py
    return notification_config