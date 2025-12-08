"""
Financial calculation tools for the portfolio analysis chatbot.
"""

import yfinance as yf
from typing import Optional, Dict, Any
from datetime import datetime
import numpy as np
import pandas as pd



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

def get_portfolio_value(portfolio: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates total portfolio market value.
    
    Args:
        portfolio: dict like {"AAPL": 10, "TSLA": 5}
    """
    total_value = 0
    breakdown = {}

    for ticker, shares in portfolio.items():
        price_data = get_stock_price(ticker)

        if price_data["success"]:
            value = shares * price_data["price"]
            breakdown[ticker] = {
                "shares": shares,
                "price": price_data["price"],
                "value": round(value, 2)
            }
            total_value += value
        else:
            breakdown[ticker] = {
                "shares": shares,
                "error": price_data["error"]
            }

    return {
        "total_value": round(total_value, 2),
        "breakdown": breakdown,
        "timestamp": datetime.now().isoformat(),
        "success": True
    }

import numpy as np

def get_stock_volatility(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """
    Calculates historical volatility of a stock.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        returns = hist["Close"].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # annualized

        return {
            "ticker": ticker.upper(),
            "volatility": round(float(volatility), 4),
            "period": period,
            "success": True
        }

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "volatility": None,
            "success": False,
            "error": str(e)
        }

def get_stock_beta(ticker: str, market_ticker: str = "^GSPC", period: str = "1y") -> Dict[str, Any]:
    """
    Calculates beta versus market (default S&P 500).
    """
    try:
        stock = yf.Ticker(ticker).history(period=period)["Close"].pct_change().dropna()
        market = yf.Ticker(market_ticker).history(period=period)["Close"].pct_change().dropna()

        min_len = min(len(stock), len(market))
        stock, market = stock[-min_len:], market[-min_len:]

        covariance = np.cov(stock, market)[0][1]
        beta = covariance / np.var(market)

        return {
            "ticker": ticker.upper(),
            "beta": round(float(beta), 4),
            "market": market_ticker,
            "success": True
        }

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "beta": None,
            "success": False,
            "error": str(e)
        }

def get_portfolio_diversification(portfolio: Dict[str, float], period="1y") -> Dict[str, Any]:
    """
    Computes diversification via correlation matrix.
    """
    try:
        returns = {}

        for ticker in portfolio:
            hist = yf.Ticker(ticker).history(period=period)["Close"].pct_change().dropna()
            returns[ticker.upper()] = hist

        df = pd.DataFrame(returns).dropna()
        corr_matrix = df.corr()

        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()

        return {
            "average_correlation": round(float(avg_corr), 4),
            "diversification_score": round(1 - avg_corr, 4),
            "correlation_matrix": corr_matrix.round(3).to_dict(),
            "success": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def rebalance_equal_weight(portfolio: Dict[str, float]) -> Dict[str, Any]:
    """
    Suggests equal-weight rebalancing.
    """
    num_assets = len(portfolio)
    weight = 1 / num_assets

    suggestions = {ticker: round(weight, 4) for ticker in portfolio}

    return {
        "rebalance_type": "equal_weight",
        "target_weights": suggestions,
        "success": True
    }
