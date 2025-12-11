"""
Main entry point for the Stock Portfolio Chatbot (CLI).
Updated to support:
- Smart rebalancing (risk profile)
- Stock suggestions (growth/income/stability)
- Portfolio adjustment recommendations
- Natural-language portfolio extraction
"""

import os
import sys
import re
from typing import Dict

# PATH SETUP
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ENVIRONMENT SETUP
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
load_dotenv(env_path)

# LANGCHAIN
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# IMPORT TOOLS
from src.tools.stock_tools import (
    get_stock_price,
    get_multiple_stock_prices,
    get_portfolio_value,
    get_stock_volatility,
    get_stock_beta,
    get_portfolio_diversification,
    rebalance_equal_weight,
    rebalance_by_risk_profile,
    suggest_stocks_by_goal,
    recommend_portfolio_adjustments
)

# ---------------------------------------------------------------
# TOOL WRAPPERS
# ---------------------------------------------------------------
@tool("get_stock_price", return_direct=False)
def fetch_stock_price(ticker: str):
    return get_stock_price(ticker)

@tool("get_multiple_stock_prices", return_direct=False)
def fetch_multiple_stock_prices(tickers: str):
    if isinstance(tickers, str):
        tickers = [
            t.strip().upper()
            for t in tickers.replace("[","").replace("]","").replace("'","").split(",")
        ]
    return get_multiple_stock_prices(tickers)

@tool("get_stock_volatility", return_direct=False)
def fetch_stock_volatility(ticker: str):
    return get_stock_volatility(ticker)

@tool("get_stock_beta", return_direct=False)
def fetch_stock_beta(ticker: str):
    return get_stock_beta(ticker)

@tool("get_portfolio_value", return_direct=False)
def fetch_portfolio_value(portfolio: dict):
    return get_portfolio_value(portfolio)

@tool("get_portfolio_diversification", return_direct=False)
def fetch_portfolio_diversification(portfolio: dict):
    return get_portfolio_diversification(portfolio)

@tool("rebalance_equal_weight", return_direct=False)
def fetch_rebalance_equal_weight(portfolio: dict):
    return rebalance_equal_weight(portfolio)

@tool("rebalance_by_risk_profile", return_direct=False)
def fetch_rebalance_by_risk_profile(portfolio: dict, risk_profile: str = "moderate"):
    return rebalance_by_risk_profile(portfolio, risk_profile)

@tool("suggest_stocks_by_goal", return_direct=False)
def fetch_suggest_stocks_by_goal(goal: str = "growth"):
    return suggest_stocks_by_goal(goal)

@tool("recommend_portfolio_adjustments", return_direct=False)
def fetch_recommend_portfolio_adjustments(portfolio: dict, goal: str = "growth"):
    return recommend_portfolio_adjustments(portfolio, goal)


# ---------------------------------------------------------------
# AGENT
# ---------------------------------------------------------------
def create_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY missing")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = [
        fetch_stock_price,
        fetch_multiple_stock_prices,
        fetch_stock_volatility,
        fetch_stock_beta,
        fetch_portfolio_value,
        fetch_portfolio_diversification,
        fetch_rebalance_equal_weight,
        fetch_rebalance_by_risk_profile,
        fetch_suggest_stocks_by_goal,
        fetch_recommend_portfolio_adjustments
    ]

    return llm.bind_tools(tools)

# ---------------------------------------------------------------
# PORTFOLIO MANAGEMENT
# ---------------------------------------------------------------
def parse_portfolio_from_text(text: str) -> Dict[str, int]:
    """Extracts tickers + shares from natural text."""
    matches = re.findall(r"(\d+)\s+([A-Za-z]+)", text)
    if not matches:
        return {}

    return {ticker.upper(): int(shares) for shares, ticker in matches}

def setup_portfolio() -> Dict[str, int]:
    print("\nWould you like to set a portfolio?\n")
    print("1. Enter manually")
    print("2. Use example")
    print("3. Skip")
    
    choice = input("Choose: ").strip()

    if choice == "1":
        return manual_portfolio()
    if choice == "2":
        return example_portfolio()
    
    print("Skipping portfolio.")
    return {}

def manual_portfolio():
    print("\nEnter holdings like: AAPL 10")
    portfolio = {}

    while True:
        line = input("Add (or 'done'): ").strip()
        if line.lower() == "done":
            break
        parsed = parse_portfolio_from_text(line)
        if parsed:
            portfolio.update(parsed)
            print("Added:", parsed)
        else:
            print("Invalid format.")
    return portfolio

def example_portfolio():
    p = {"VOO": 10, "AAPL": 20, "QQQ": 10}
    print("\nUsing example:", p)
    return p


# ---------------------------------------------------------------
# CHAT LOOP
# ---------------------------------------------------------------
def chat_with_agent(agent):
    print("\n🚀 StockBot started! Type 'exit' to quit.\n")

    user_portfolio = setup_portfolio()
    conversation = []

    if user_portfolio:
        pstr = ", ".join(f"{s} {t}" for t, s in user_portfolio.items())
        conversation.append(HumanMessage(content=f"My portfolio is {pstr}"))

    tools_map = {
        "get_stock_price": fetch_stock_price,
        "get_multiple_stock_prices": fetch_multiple_stock_prices,
        "get_stock_volatility": fetch_stock_volatility,
        "get_stock_beta": fetch_stock_beta,
        "get_portfolio_value": fetch_portfolio_value,
        "get_portfolio_diversification": fetch_portfolio_diversification,
        "rebalance_equal_weight": fetch_rebalance_equal_weight,
        "rebalance_by_risk_profile": fetch_rebalance_by_risk_profile,
        "suggest_stocks_by_goal": fetch_suggest_stocks_by_goal,
        "recommend_portfolio_adjustments": fetch_recommend_portfolio_adjustments
    }

    while True:
        msg = input("You: ").strip()

        if msg.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Auto-detect portfolio text
        extracted = parse_portfolio_from_text(msg)
        if extracted:
            user_portfolio = extracted
            print("[Portfolio updated]", user_portfolio)

        conversation.append(HumanMessage(content=msg))

        response = agent.invoke(conversation)

        if response.tool_calls:
            conversation.append(response)

            for call in response.tool_calls:
                tname = call["name"]
                targs = call["args"]
                tid = call["id"]

                if tname in ["get_portfolio_value", "get_portfolio_diversification",
                             "rebalance_equal_weight", "rebalance_by_risk_profile",
                             "recommend_portfolio_adjustments"]:
                    if "portfolio" not in targs:
                        targs["portfolio"] = user_portfolio

                try:
                    result = tools_map[tname].invoke(targs)
                except Exception as e:
                    result = {"error": str(e)}

                conversation.append(ToolMessage(content=str(result), tool_call_id=tid))

            final = agent.invoke(conversation)
            conversation.append(final)
            print("Bot:", final.content)
        else:
            conversation.append(response)
            print("Bot:", response.content)


# ---------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("Starting Stock Portfolio CLI...")
    agent = create_agent()
    chat_with_agent(agent)
