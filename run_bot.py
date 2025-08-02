#!/usr/bin/env python3
"""
SPX 0DTE Trading Bot Launcher
============================

Simple launcher script for the SPX trading bot.
Provides easy access to common operations.
"""

import sys
import subprocess
import os
from datetime import datetime

def print_banner():
    """Print bot banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    SPX 0DTE Trading Bot                      ║
    ║                         🤖📈                                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import yfinance
        import pandas
        import numpy
        import ta
        import schedule
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    """Main launcher menu"""
    print_banner()
    
    if not check_dependencies():
        sys.exit(1)
    
    print("Select an option:")
    print("1. 🧪 Test Mode (Paper Trading - Single Analysis)")
    print("2. ⏰ Scheduled Mode (Paper Trading - Daily 7 AM PST)")
    print("3. 📊 Manual Analysis (Paper Trading)")
    print("4. 🚨 Live Trading Mode (REAL MONEY - Use with caution!)")
    print("5. ⚙️  Create Environment Template")
    print("6. 📋 Show Current Configuration")
    print("7. 📈 View Recent Logs")
    print("8. ❌ Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                print("🧪 Running Test Mode...")
                subprocess.run([sys.executable, "main_trading_bot.py", "--mode", "test"])
                break
                
            elif choice == '2':
                print("⏰ Starting Scheduled Mode (Paper Trading)...")
                print("Bot will run daily at 7 AM PST. Press Ctrl+C to stop.")
                subprocess.run([sys.executable, "main_trading_bot.py", "--mode", "scheduled"])
                break
                
            elif choice == '3':
                print("📊 Running Manual Analysis...")
                subprocess.run([sys.executable, "main_trading_bot.py", "--mode", "manual"])
                break
                
            elif choice == '4':
                print("🚨 WARNING: LIVE TRADING MODE")
                print("This will trade with REAL MONEY!")
                confirm = input("Type 'YES' to confirm live trading: ").strip()
                
                if confirm == 'YES':
                    mode = input("Choose mode (scheduled/manual): ").strip().lower()
                    if mode in ['scheduled', 'manual']:
                        print(f"🚨 Starting Live Trading in {mode} mode...")
                        subprocess.run([sys.executable, "main_trading_bot.py", 
                                      "--mode", mode, "--live"])
                    else:
                        print("Invalid mode. Choose 'scheduled' or 'manual'")
                else:
                    print("Live trading cancelled.")
                break
                
            elif choice == '5':
                print("⚙️ Creating Environment Template...")
                subprocess.run([sys.executable, "main_trading_bot.py", "--create-env"])
                print("Created .env.template file. Copy to .env and configure.")
                break
                
            elif choice == '6':
                print("📋 Current Configuration:")
                show_config()
                break
                
            elif choice == '7':
                print("📈 Recent Logs:")
                show_recent_logs()
                break
                
            elif choice == '8':
                print("👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1-8.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")

def show_config():
    """Show current configuration"""
    try:
        from config import Config
        config = Config()
        
        print(f"  IB Host: {config.IB_HOST}")
        print(f"  IB Port: {config.IB_PORT}")
        print(f"  Spread Width: ${config.SPREAD_WIDTH}")
        print(f"  Min Credit: ${config.MIN_CREDIT}")
        print(f"  Max Risk per Trade: ${config.MAX_RISK_PER_TRADE}")
        print(f"  Target Delta: {config.TARGET_DELTA}")
        print(f"  Min Probability: {config.MIN_PROBABILITY:.0%}")
        
        # Check environment file
        if os.path.exists('.env'):
            print("  ✅ .env file found")
        else:
            print("  ❌ .env file not found - run option 5 to create template")
            
    except Exception as e:
        print(f"  ❌ Error reading config: {e}")

def show_recent_logs():
    """Show recent log entries"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            print("  📁 No logs directory found")
            return
            
        # Find most recent log file
        log_files = [f for f in os.listdir(log_dir) if f.startswith("trading_bot_")]
        if not log_files:
            print("  📄 No log files found")
            return
            
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(log_dir, latest_log)
        
        print(f"  📄 Latest log: {latest_log}")
        print("  " + "="*50)
        
        # Show last 20 lines
        with open(log_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(f"  {line.rstrip()}")
                
    except Exception as e:
        print(f"  ❌ Error reading logs: {e}")

if __name__ == "__main__":
    main()