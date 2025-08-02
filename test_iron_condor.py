#!/usr/bin/env python3
"""
Test script for Iron Condor strategy
====================================

This script demonstrates the Iron Condor functionality
for sideways/range-bound market conditions.
"""

import asyncio
import sys
from datetime import datetime
import logging

# Import our modules
from market_analyzer import MarketAnalyzer
from strategy_engine import StrategyEngine
from notifications import NotificationManager

def setup_logging():
    """Set up logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

async def test_iron_condor():
    """Test Iron Condor strategy with current market conditions"""
    print("🦅 Testing SPX Iron Condor Strategy")
    print("=" * 50)
    
    # Initialize components
    market_analyzer = MarketAnalyzer()
    strategy_engine = StrategyEngine()
    notification_manager = NotificationManager()
    
    try:
        # Get market analysis
        print("📊 Analyzing current market conditions...")
        market_analysis = market_analyzer.get_market_analysis()
        
        if market_analysis is None:
            print("❌ Failed to get market analysis")
            return
        
        # Display market analysis
        print(f"\n📈 Market Analysis Results:")
        print(f"  Direction: {market_analysis['direction']}")
        print(f"  SPX Price: ${market_analysis['spx_price']:.2f}")
        print(f"  VIX Level: {market_analysis['vix_level']:.1f}")
        print(f"  RSI: {market_analysis['rsi']:.1f}")
        print(f"  BB Position: {market_analysis.get('bb_position', 0):.2f}")
        print(f"  Volume Ratio: {market_analysis.get('volume_ratio', 1):.2f}")
        
        # Test Iron Condor strategy
        print(f"\n🦅 Testing Iron Condor Strategy...")
        
        if market_analysis['direction'] == 'SIDEWAYS':
            print("✅ Market is SIDEWAYS - Perfect for Iron Condor!")
            
            # Find optimal iron condor
            iron_condor = strategy_engine.find_optimal_iron_condor(market_analysis)
            
            if iron_condor:
                print(f"\n🎯 Iron Condor Found!")
                print(f"  Optimization Score: {iron_condor.get('optimization_score', 0):.0f}/100")
                
                # Display trade summary
                trade_summary = strategy_engine.format_trade_summary(iron_condor)
                print(f"\n{trade_summary}")
                
                # Send notification if enabled
                try:
                    notification_manager.send_trade_notification(iron_condor, "TEST")
                    print("📱 Test notification sent!")
                except:
                    print("📱 Notifications not configured (this is normal for testing)")
                
            else:
                print("❌ No suitable Iron Condor found")
                print("   Market conditions don't meet Iron Condor criteria")
                
        else:
            print(f"⚠️  Market is {market_analysis['direction']} - Not ideal for Iron Condor")
            print("   Iron Condor works best in SIDEWAYS markets")
            
            # Force test Iron Condor anyway for demonstration
            print("\n🧪 Force-testing Iron Condor for demonstration...")
            
            # Temporarily override market direction
            test_analysis = market_analysis.copy()
            test_analysis['direction'] = 'SIDEWAYS'
            test_analysis['rsi'] = 50  # Neutral RSI
            test_analysis['vix_level'] = min(max(test_analysis['vix_level'], 15), 30)  # Clamp VIX
            
            iron_condor = strategy_engine.find_optimal_iron_condor(test_analysis)
            
            if iron_condor:
                print("✅ Demo Iron Condor created with adjusted conditions!")
                trade_summary = strategy_engine.format_trade_summary(iron_condor)
                print(f"\n{trade_summary}")
            else:
                print("❌ Even with adjusted conditions, no Iron Condor qualified")
        
        # Test all strategies for comparison
        print(f"\n📊 Comparing All Strategies:")
        all_recommendations = strategy_engine.generate_trade_recommendations(market_analysis)
        
        if all_recommendations:
            for i, trade in enumerate(all_recommendations, 1):
                print(f"\n  Strategy {i}: {trade['strategy'].upper().replace('_', ' ')}")
                print(f"    Recommendation: {trade['recommendation']}")
                print(f"    Prob of Profit: {trade['prob_profit']:.1%}")
                if 'optimization_score' in trade:
                    print(f"    Optimization Score: {trade['optimization_score']:.0f}/100")
        else:
            print("  No strategies recommended for current conditions")
        
        print(f"\n✅ Iron Condor test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    setup_logging()
    
    print("Starting Iron Condor Strategy Test...")
    print("This will analyze current market conditions and test Iron Condor logic")
    print()
    
    # Run the test
    asyncio.run(test_iron_condor())

if __name__ == "__main__":
    main()