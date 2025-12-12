"""
Financial calculation & portfolio analysis tools
for the Stock Portfolio Chatbot.

Includes:
- Price lookup (yfinance)
- Portfolio value
- Volatility and beta
- Diversification scoring (sector concentration)
- Smart rebalancing (risk profile)
- Stock suggestions (based on user goals)
- Portfolio adjustment recommendations
"""

import yfinance as yf
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

def fetch_ticker(ticker: str):
    try:
        return yf.Ticker(ticker)
    except Exception:
        return None

def get_stock_price(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )

        if price is None:
            raise ValueError("No price available")

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "currency": info.get("currency", "USD"),
            "company_name": info.get("longName", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "success": False,
            "error": f"Price fetch failed: {e}"
        }

def get_multiple_stock_prices(tickers: list) -> Dict[str, Dict[str, Any]]:
    results = {}
    for t in tickers:
        results[t.upper()] = get_stock_price(t)
    return results


def get_portfolio_value(portfolio: Dict[str, int]) -> Dict[str, Any]:
    total = 0
    details = {}

    for ticker, shares in portfolio.items():
        quote = get_stock_price(ticker)

        if not quote["success"]:
            details[ticker] = quote
            continue

        value = quote["price"] * shares
        total += value

        details[ticker] = {
            "shares": shares,
            "price": quote["price"],
            "value": round(value, 2),
        }

    return {
        "portfolio_value": round(total, 2),
        "breakdown": details,
        "success": True
    }

def get_stock_volatility(ticker: str) -> Dict[str, Any]:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")["Close"]

        if hist.empty:
            raise ValueError("No price history")

        daily_returns = np.log(hist / hist.shift(1)).dropna()
        vol = daily_returns.std() * np.sqrt(252)

        return {
            "ticker": ticker.upper(),
            "volatility": round(float(vol), 4),
            "success": True
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "success": False, "error": str(e)}

def get_stock_beta(ticker: str) -> Dict[str, Any]:
    try:
        stock = yf.Ticker(ticker)
        stock_hist = stock.history(period="1y")["Close"]
        spy_hist = yf.Ticker("SPY").history(period="1y")["Close"]

        returns_stock = np.log(stock_hist / stock_hist.shift(1)).dropna()
        returns_spy = np.log(spy_hist / spy_hist.shift(1)).dropna()

        min_len = min(len(returns_stock), len(returns_spy))
        returns_stock = returns_stock[-min_len:]
        returns_spy = returns_spy[-min_len:]

        cov = np.cov(returns_stock, returns_spy)[0][1]
        var = np.var(returns_spy)

        beta = cov / var

        return {
            "ticker": ticker.upper(),
            "beta": round(float(beta), 3),
            "success": True
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "success": False, "error": str(e)}


def get_portfolio_diversification(portfolio: Dict[str, int]) -> Dict[str, Any]:
    sectors = {}
    total_value = 0
    details = {}

    for ticker, shares in portfolio.items():
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is None:
            continue

        value = price * shares
        total_value += value

        sector = info.get("sector", "Unknown")
        sectors.setdefault(sector, 0)
        sectors[sector] += value

        details[ticker] = {
            "shares": shares,
            "sector": sector,
            "value": round(value, 2)
        }

    if total_value == 0:
        return {
            "success": False,
            "error": "No valid stock prices found."
        }

    weights = {sector: value / total_value for sector, value in sectors.items()}

    hhi = sum(w * w for w in weights.values())
    score = 1 - hhi

    return {
        "success": True,
        "diversification_score": round(score, 4),
        "sector_weights": weights,
        "details": details
    }

def rebalance_equal_weight(portfolio: Dict[str, int]) -> Dict[str, Any]:
    value_data = get_portfolio_value(portfolio)
    total_value = value_data["portfolio_value"]

    n = len(portfolio)
    if n == 0:
        return {"success": False, "error": "Portfolio empty"}

    target = total_value / n

    adjustments = {}
    for ticker in portfolio:
        current = value_data["breakdown"][ticker]["value"]
        diff = target - current
        adjustments[ticker] = round(diff, 2)

    return {
        "success": True,
        "strategy": "equal_weight",
        "target_value_each": round(target, 2),
        "adjustments": adjustments
    }

RISK_PROFILES = {
    "conservative": {
        "VOO": 0.50, "BND": 0.30, "GLD": 0.10, "AAPL": 0.05, "QQQ": 0.05
    },
    "moderate": {
        "VOO": 0.40, "QQQ": 0.25, "AAPL": 0.20, "BND": 0.10, "GLD": 0.05
    },
    "aggressive": {
        "QQQ": 0.40, "AAPL": 0.30, "VOO": 0.20, "NVDA": 0.10
    }
}

def rebalance_by_risk_profile(portfolio: Dict[str, int], risk_profile: str):
    risk_profile = risk_profile.lower()
    
    if risk_profile not in RISK_PROFILES:
        return {"success": False, "error": f"Unknown risk profile '{risk_profile}'"}

    targets = RISK_PROFILES[risk_profile]
    current_value = get_portfolio_value(portfolio)
    total = current_value["portfolio_value"]

    target_allocations = {t: round(total * w, 2) for t, w in targets.items()}

    return {
        "success": True,
        "risk_profile": risk_profile,
        "target_allocations": target_allocations,
        "notes": "You should shift toward these allocations to match risk profile."
    }

GOAL_SUGGESTIONS = {
    "growth": ["NVDA", "TSLA", "AAPL", "AMD"],
    "income": ["JNJ", "PG", "KO", "O", "VZ"],
    "value": ["BRK-B", "JPM", "CVX", "WMT"],
    "stability": ["VOO", "BND", "XLU"]
}

def suggest_stocks_by_goal(goal: str):
    goal = goal.lower()
    if goal not in GOAL_SUGGESTIONS:
        return {"success": False, "error": f"Unknown goal '{goal}'"}

    return {
        "success": True,
        "goal": goal,
        "suggestions": GOAL_SUGGESTIONS[goal]
    }

def recommend_portfolio_adjustments(portfolio: Dict[str, int], goal: str):
    suggestion = suggest_stocks_by_goal(goal)

    if not suggestion["success"]:
        return suggestion

    diversification = get_portfolio_diversification(portfolio)

    return {
        "success": True,
        "goal": goal,
        "suggestions": suggestion["suggestions"],
        "diversification_score": diversification.get("diversification_score"),
        "notes": (
            "These stocks align with your goal and may improve diversification "
            "depending on your current holdings."
        )
    }

def rebalance_by_risk_profile(portfolio: dict, risk: str = "moderate") -> dict:
    risk = risk.lower().strip()

    profiles = {
        "conservative": {
            "equity": 0.40,
            "bonds": 0.50,
            "alternatives": 0.10
        },
        "moderate": {
            "equity": 0.60,
            "bonds": 0.30,
            "alternatives": 0.10
        },
        "aggressive": {
            "equity": 0.85,
            "bonds": 0.10,
            "alternatives": 0.05
        }
    }

    if risk not in profiles:
        return {
            "success": False,
            "error": f"Unknown risk profile '{risk}'. Use conservative, moderate, or aggressive."
        }

    target = profiles[risk]

    return {
        "success": True,
        "risk_profile": risk,
        "target_allocations": target,
        "message": f"Rebalanced portfolio using {risk} profile."
    }


def suggest_stocks_for_goal(goal: str) -> dict:

    goal = goal.lower().strip()

    suggestions = {
        "growth": ["NVDA", "AAPL", "MSFT", "META", "TSLA"],
        "income": ["JNJ", "KO", "PG", "T", "VZ"],
        "balanced": ["VOO", "QQQ", "BND", "VNQ"],
        "tech": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD"],
        "value": ["BRK.B", "UNH", "JPM", "XOM", "CVX"]
    }

    if goal not in suggestions:
        return {
            "success": False,
            "error": f"Unknown goal '{goal}'. Try growth, income, balanced, tech, or value."
        }

    return {
        "success": True,
        "goal": goal,
        "suggested_stocks": suggestions[goal],
        "message": f"Here are stocks aligned with a {goal} investing strategy."
    }
