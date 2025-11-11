"""
Unit tests for stock price fetching tools.
Run with: pytest test_stock_tools.py
or: python test_stock_tools.py
"""

import unittest
from stock_tools import get_stock_price, get_multiple_stock_prices


class TestStockPriceFetcher(unittest.TestCase):
    """Test cases for stock price fetching functionality"""
    
    def test_valid_stock_ticker(self):
        """Test fetching a valid stock ticker (AAPL)"""
        result = get_stock_price('AAPL')
        
        # Check structure
        self.assertIn('ticker', result)
        self.assertIn('price', result)
        self.assertIn('success', result)
        self.assertIn('timestamp', result)
        
        # Check values if successful
        if result['success']:
            self.assertEqual(result['ticker'], 'AAPL')
            self.assertIsNotNone(result['price'])
            self.assertIsInstance(result['price'], (int, float))
            self.assertGreater(result['price'], 0)
            print(f"✓ AAPL Price: ${result['price']}")
        else:
            print(f"✗ AAPL fetch failed: {result['error']}")
    
    def test_case_insensitive(self):
        """Test that ticker symbols are case insensitive"""
        result_lower = get_stock_price('aapl')
        result_upper = get_stock_price('AAPL')
        
        self.assertEqual(result_lower['ticker'], 'AAPL')
        self.assertEqual(result_upper['ticker'], 'AAPL')
    
    def test_invalid_ticker(self):
        """Test handling of invalid ticker symbol"""
        result = get_stock_price('INVALID_TICKER_XYZ123')
        
        # Should return error gracefully
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])
        self.assertIsNone(result['price'])
        print(f"✓ Invalid ticker handled correctly: {result['error']}")
    
    def test_multiple_stocks(self):
        """Test fetching multiple stocks at once"""
        tickers = ['AAPL', 'GOOGL', 'MSFT']
        results = get_multiple_stock_prices(tickers)
        
        # Check all tickers are in results
        self.assertEqual(len(results), 3)
        for ticker in tickers:
            self.assertIn(ticker, results)
            self.assertIn('price', results[ticker])
            self.assertIn('success', results[ticker])
        
        # Print results
        print("\nMultiple Stock Prices:")
        for ticker, data in results.items():
            if data['success']:
                print(f"  {ticker}: ${data['price']} ({data['company_name']})")
            else:
                print(f"  {ticker}: Error - {data['error']}")
    
    def test_response_structure(self):
        """Test that response has all required fields"""
        result = get_stock_price('AAPL')
        
        required_fields = ['ticker', 'price', 'currency', 'company_name', 
                          'timestamp', 'success', 'error']
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing field: {field}")
        
        print(f"✓ All required fields present in response")
    
    def test_different_stocks(self):
        """Test a variety of stock tickers"""
        test_tickers = ['TSLA', 'AMZN', 'META', 'NVDA']
        
        print("\nTesting various stocks:")
        for ticker in test_tickers:
            result = get_stock_price(ticker)
            if result['success']:
                print(f"  ✓ {ticker}: ${result['price']}")
            else:
                print(f"  ✗ {ticker}: {result['error']}")


def run_manual_tests():
    """Manual testing function for quick checks"""
    print("=" * 50)
    print("MANUAL STOCK PRICE FETCHER TESTS")
    print("=" * 50)
    
    # Test 1: Single stock
    print("\n1. Testing single stock (AAPL):")
    result = get_stock_price('AAPL')
    if result['success']:
        print(f"   ✓ Success!")
        print(f"   Ticker: {result['ticker']}")
        print(f"   Company: {result['company_name']}")
        print(f"   Price: ${result['price']} {result['currency']}")
        print(f"   Timestamp: {result['timestamp']}")
    else:
        print(f"   ✗ Failed: {result['error']}")
    
    # Test 2: Multiple stocks
    print("\n2. Testing multiple stocks:")
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    results = get_multiple_stock_prices(tickers)
    
    successful = 0
    failed = 0
    
    for ticker, data in results.items():
        if data['success']:
            print(f"   ✓ {ticker:6s}: ${data['price']:8.2f} - {data['company_name']}")
            successful += 1
        else:
            print(f"   ✗ {ticker:6s}: {data['error']}")
            failed += 1
    
    print(f"\n   Summary: {successful} successful, {failed} failed")
    
    # Test 3: Invalid ticker
    print("\n3. Testing invalid ticker:")
    result = get_stock_price('FAKE_TICKER_123')
    if not result['success']:
        print(f"   ✓ Correctly handled invalid ticker")
        print(f"   Error message: {result['error']}")
    else:
        print(f"   ✗ Should have failed for invalid ticker")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Run manual tests
    run_manual_tests()
    
    print("\n\nRunning unit tests...")
    print("=" * 50)
    
    # Run unittest suite
    unittest.main(verbosity=2)