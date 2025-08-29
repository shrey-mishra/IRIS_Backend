#!/usr/bin/env python3
"""
Test script for Auto Trading functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_market_signals():
    """Test market signals endpoint"""
    print("🔍 Testing Market Signals...")
    
    try:
        # Test individual symbol
        response = requests.get(f"{BASE_URL}/trading/market-signals?symbol=BTC/USDT")
        print(f"Individual BTC/USDT signal: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Signal: {data.get('signal')}")
            print(f"  Strength: {data.get('strength')}")
            print(f"  Factors: {data.get('factors')}")
        else:
            print(f"  Error: {response.text}")
            
        # Test all symbols
        response = requests.get(f"{BASE_URL}/trading/market-signals-all")
        print(f"\nAll market signals: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Total signals: {len(data)}")
            for signal in data:
                print(f"  {signal['symbol']}: {signal['signal']} (strength: {signal['strength']})")
        else:
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Market signals test failed: {e}")

def test_ai_performance():
    """Test AI performance endpoint"""
    print("\n📊 Testing AI Performance...")
    
    try:
        response = requests.get(f"{BASE_URL}/trading/ai-performance")
        print(f"AI Performance: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Total trades: {data.get('total_trades')}")
            print(f"  Success rate: {data.get('success_rate')}%")
            print(f"  Total profit: ${data.get('total_profit')}")
        else:
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"❌ AI Performance test failed: {e}")

def test_technical_indicators():
    """Test if technical indicators are working"""
    print("\n📈 Testing Technical Indicators...")
    
    try:
        # Test with a simple symbol
        response = requests.get(f"{BASE_URL}/trading/market-signals?symbol=ETH/USDT")
        print(f"ETH/USDT Technical Analysis: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Signal: {data.get('signal')}")
            print(f"  Strength: {data.get('strength')}")
            if 'indicators' in data and data['indicators']:
                print(f"  Indicators available: {list(data['indicators'].keys())}")
            else:
                print(f"  No indicators available")
        else:
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Technical indicators test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Auto Trading Backend Functionality\n")
    
    test_market_signals()
    test_ai_performance()
    test_technical_indicators()
    
    print("\n✅ Test completed!")




