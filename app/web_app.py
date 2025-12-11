"""
Flask web application for Stock Portfolio Chatbot.
"""

from flask import Flask, render_template, request, jsonify, session
import os
import sys
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- ENVIRONMENT SETUP ---
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
load_dotenv(env_path)

# --- LANGCHAIN / OPENAI ---
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# --- IMPORT TOOLS ---
from src.tools.stock_tools import (
    get_stock_price,
    get_multiple_stock_prices,
    get_portfolio_value,
    get_stock_volatility,
    get_stock_beta,
    get_portfolio_diversification,
    rebalance_equal_weight,
    rebalance_by_risk_profile,
    suggest_stocks_for_goal
)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'my-chatbot-secret-key-2025')

# -------------------------------------------------------------------------
# TOOL WRAPPERS
# -------------------------------------------------------------------------

@tool("get_stock_price")
def fetch_stock_price(ticker: str) -> dict:
    """Get current price for a ticker."""
    return get_stock_price(ticker)


@tool("get_multiple_stock_prices")
def fetch_multiple_stock_prices(tickers: str) -> dict:
    """Get prices for multiple tickers."""
    if isinstance(tickers, str):
        tickers = [t.strip().upper() for t in tickers.replace("[", "").replace("]", "").replace("'", "").split(",")]
    return get_multiple_stock_prices(tickers)


@tool("get_stock_volatility")
def fetch_stock_volatility(ticker: str) -> dict:
    """Get annualized volatility of a stock."""
    return get_stock_volatility(ticker)


@tool("get_stock_beta")
def fetch_stock_beta(ticker: str) -> dict:
    """Get beta of a stock."""
    return get_stock_beta(ticker)


@tool("get_portfolio_value")
def fetch_portfolio_value(portfolio: dict) -> dict:
    """Compute total value of a portfolio."""
    return get_portfolio_value(portfolio)


@tool("get_portfolio_diversification")
def fetch_portfolio_diversification(portfolio: dict) -> dict:
    """Compute diversification score."""
    return get_portfolio_diversification(portfolio)


@tool("rebalance_equal_weight")
def fetch_rebalance_equal_weight(portfolio: dict) -> dict:
    """Equal-weight rebalancing recommendation."""
    return rebalance_equal_weight(portfolio)


@tool("rebalance_by_risk_profile")
def fetch_rebalance_by_risk_profile(portfolio: dict, risk: str = "moderate") -> dict:
    """Smart rebalancing based on risk appetite."""
    return rebalance_by_risk_profile(portfolio, risk)


@tool("suggest_stocks_for_goal")
def fetch_suggest_stocks(goal: str) -> dict:
    """Suggest stocks based on a user's investing goal."""
    return suggest_stocks_for_goal(goal)

# -------------------------------------------------------------------------
# INITIALIZE AGENT
# -------------------------------------------------------------------------

def create_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set.")

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
        fetch_suggest_stocks
    ]

    return llm.bind_tools(tools)

try:
    llm_with_tools = create_agent()

    tools_map = {
        "get_stock_price": fetch_stock_price,
        "get_multiple_stock_prices": fetch_multiple_stock_prices,
        "get_stock_volatility": fetch_stock_volatility,
        "get_stock_beta": fetch_stock_beta,
        "get_portfolio_value": fetch_portfolio_value,
        "get_portfolio_diversification": fetch_portfolio_diversification,
        "rebalance_equal_weight": fetch_rebalance_equal_weight,
        "rebalance_by_risk_profile": fetch_rebalance_by_risk_profile,
        "suggest_stocks_for_goal": fetch_suggest_stocks
    }

except Exception as e:
    print(f"Error initializing agent: {e}")
    llm_with_tools = None
    tools_map = {}

# -------------------------------------------------------------------------
# FLASK ROUTES
# -------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

# Holds all conversation histories
conversations = {}


# NEW: Store portfolio separately
@app.route("/set_portfolio", methods=["POST"])
def set_portfolio():
    try:
        data = request.json
        portfolio = data.get("portfolio")

        if not portfolio:
            return jsonify({"status": "error", "message": "Invalid portfolio"}), 400

        session["portfolio"] = portfolio
        print("[PORTFOLIO SAVED]", session["portfolio"])

        return jsonify({"status": "success"})

    except Exception as e:
        print("set_portfolio error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_portfolio", methods=["GET"])
def get_portfolio():
    portfolio = session.get("portfolio", {})
    return jsonify({
        "status": "success",
        "has_portfolio": bool(portfolio),
        "portfolio": portfolio
    })

# -------------------------------------------------------------------------
# CHAT ENDPOINT
# -------------------------------------------------------------------------

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not llm_with_tools:
        return jsonify({"message": "LLM not initialized", "status": "error"}), 500

    # Assign session conversation ID
    if "conversation_id" not in session:
        session["conversation_id"] = str(uuid.uuid4())

    conv_id = session["conversation_id"]

    # Initialize conversation history
    if conv_id not in conversations:
        conversations[conv_id] = []

    # Add user message
    conversations[conv_id].append(HumanMessage(content=user_message))

    try:
        # 1: First LLM response (may contain tool calls)
        response = llm_with_tools.invoke(conversations[conv_id])

        tool_logs = []

        if response.tool_calls:
            conversations[conv_id].append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                # Auto-inject portfolio
                if tool_name in [
                    "get_portfolio_value",
                    "get_portfolio_diversification",
                    "rebalance_equal_weight",
                    "rebalance_by_risk_profile"
                ]:
                    stored = session.get("portfolio")
                    if not stored:
                        raise ValueError("No portfolio saved yet.")
                    tool_args["portfolio"] = stored

                # Run tool
                result = tools_map[tool_name].invoke(tool_args)

                tool_logs.append({"tool": tool_name, "args": tool_args, "result": str(result)})

                conversations[conv_id].append(
                    ToolMessage(content=str(result), tool_call_id=tool_call_id)
                )

            # 2: Final model response after tools
            final = llm_with_tools.invoke(conversations[conv_id])
            conversations[conv_id].append(final)
            bot_message = final.content
        else:
            conversations[conv_id].append(response)
            bot_message = response.content

        return jsonify({
            "message": bot_message,
            "status": "success",
            "tool_logs": tool_logs
        })

    except Exception as e:
        print("Chat endpoint error:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# -------------------------------------------------------------------------
# RESET HISTORY
# -------------------------------------------------------------------------

@app.route('/reset', methods=['POST'])
def reset():
    session.pop("conversation_id", None)
    session.pop("portfolio", None)
    return jsonify({"status": "success"})


# -------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
