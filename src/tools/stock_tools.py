"""
Financial calculation tools for the portfolio analysis chatbot.
"""

import yfinance as yf
from typing import Optional, Dict, Any
from datetime import datetime


def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Fetches the current stock price for a given ticker symbol.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')
    
    Returns:
        Dict containing:
            - ticker: Stock symbol
            - price: Current price
            - currency: Currency of the price
            - timestamp: When the data was retrieved
            - success: Whether the fetch was successful
            - error: Error message if unsuccessful
    
    Example:
        >>> get_stock_price('AAPL')
        {'ticker': 'AAPL', 'price': 178.23, 'currency': 'USD', ...}
    """
    try:
        # Create ticker object
        stock = yf.Ticker(ticker.upper())
        
        # Get current data
        info = stock.info
        
        # Try to get the current price (multiple fallback options)
        current_price = (
            info.get('currentPrice') or 
            info.get('regularMarketPrice') or 
            info.get('previousClose')
        )
        
        if current_price is None:
            return {
                'ticker': ticker.upper(),
                'price': None,
                'currency': None,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': f'Could not retrieve price data for {ticker}'
            }
        
        return {
            'ticker': ticker.upper(),
            'price': round(current_price, 2),
            'currency': info.get('currency', 'USD'),
            'company_name': info.get('longName', 'Unknown'),
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'error': None
        }
    
    except Exception as e:
        return {
            'ticker': ticker.upper(),
            'price': None,
            'currency': None,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': str(e)
        }


def get_multiple_stock_prices(tickers: list) -> Dict[str, Dict[str, Any]]:
    """
    Fetches current stock prices for multiple ticker symbols.
    
    Args:
        tickers (list): List of stock ticker symbols
    
    Returns:
        Dict mapping each ticker to its price data
    
    Example:
        >>> get_multiple_stock_prices(['AAPL', 'GOOGL', 'MSFT'])
        {'AAPL': {...}, 'GOOGL': {...}, 'MSFT': {...}}
    """
    results = {}
    for ticker in tickers:
        results[ticker.upper()] = get_stock_price(ticker)
    return results