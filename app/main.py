"""
Main entry point for the Stock Portfolio Chatbot.
Integrates LangChain with custom financial tools in src/tools/stock_tools.py.
"""

import os
import sys
from typing import List

# --- PATH SETUP ---
# Ensure we can import from the src folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- ENVIRONMENT SETUP ---
from dotenv import load_dotenv
import os

# Load .env file from the config folder
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
load_dotenv(env_path)

# --- LANGCHAIN + OPENAI ---
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# --- IMPORT YOUR TOOLS ---
from src.tools.stock_tools import get_stock_price, get_multiple_stock_prices, get_portfolio_value, get_stock_volatility, get_stock_beta, get_portfolio_diversification, rebalance_equal_weight


# --- DEFINE TOOL WRAPPERS FOR LANGCHAIN ---

@tool("get_stock_price", return_direct=False)
def fetch_stock_price(ticker: str) -> dict:
    """
    Fetch the current price of a given stock ticker symbol.
    Example: 'AAPL'
    """
    return get_stock_price(ticker)


@tool("get_multiple_stock_prices", return_direct=False)
def fetch_multiple_stock_prices(tickers: str) -> dict:
    """
    Fetch current prices for multiple ticker symbols.
    Example: ['AAPL', 'GOOGL', 'MSFT']
    """
    if isinstance(tickers, str):
        # Clean and split user input safely
        tickers = [t.strip().upper() for t in tickers.replace("[", "").replace("]", "").replace("'", "").split(",")]
    return get_multiple_stock_prices(tickers)

@tool("get_stock_volatility", return_direct=False)
def fetch_stock_volatility(ticker: str) -> dict:
    """Gets annualized volatility of a stock."""
    return get_stock_volatility(ticker)


@tool("get_stock_beta", return_direct=False)
def fetch_stock_beta(ticker: str) -> dict:
    """Gets beta of a stock vs the market."""
    return get_stock_beta(ticker)


@tool("get_portfolio_value", return_direct=False)
def fetch_portfolio_value(portfolio: dict) -> dict:
    """Gets total market value of a portfolio."""
    return get_portfolio_value(portfolio)


@tool("get_portfolio_diversification", return_direct=False)
def fetch_portfolio_diversification(portfolio: dict) -> dict:
    """Computes portfolio diversification score."""
    return get_portfolio_diversification(portfolio)


@tool("rebalance_equal_weight", return_direct=False)
def fetch_rebalance_equal_weight(portfolio: dict) -> dict:
    """Suggests equal-weight rebalancing."""
    return rebalance_equal_weight(portfolio)

# --- INITIALIZE AGENT ---

def create_agent():
    """Initializes the LangChain LLM with tools for stock analysis."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Set it in your environment or .env file.")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = [fetch_stock_price, fetch_multiple_stock_prices, fetch_stock_volatility,        # ✅ new
    fetch_stock_beta,
    fetch_portfolio_value,
    fetch_portfolio_diversification,
    fetch_rebalance_equal_weight]
    
    # Bind tools to the LLM for function calling
    llm_with_tools = llm.bind_tools(tools)

    return llm_with_tools


# --- CHAT LOOP ---

def chat_with_agent(llm_with_tools):
    """Runs an interactive chat loop in the terminal."""
    print("💬 StockBot is ready! Type 'exit' to quit.\n")
    print("Ask me about stock prices! Example: 'What is the price of AAPL?'\n")

    tools_map = {
        "get_stock_price": fetch_stock_price,
        "get_multiple_stock_prices": fetch_multiple_stock_prices,
        "get_stock_volatility": fetch_stock_volatility,       
        "get_stock_beta": fetch_stock_beta,
        "get_portfolio_value": fetch_portfolio_value,
        "get_portfolio_diversification": fetch_portfolio_diversification,
        "rebalance_equal_weight": fetch_rebalance_equal_weight
    }

    # --- INITIALIZE CONVERSATION HISTORY ---
    conversation_history = []
    print("[SYSTEM] Conversation history initialized.\n")

    while True:
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in {"exit", "quit"}:
            print(f"\n[SYSTEM] Session ended. Total messages exchanged: {len(conversation_history)}")
            print("Goodbye! 👋")
            break
        
        # Check for reset command
        if user_input.lower() in {"reset", "clear", "new"}:
            conversation_history = []
            print("\n[SYSTEM] ✅ Conversation history cleared. Starting fresh!\n")
            continue
        
        # Skip empty inputs
        if not user_input:
            continue

        try:
             # --- ADD USER MESSAGE TO HISTORY ---
            conversation_history.append(HumanMessage(content=user_input))

            # --- INVOKE LLM WITH FULL CONVERSATION HISTORY ---
            response = llm_with_tools.invoke(conversation_history)
            
            # Check if the model wants to call a tool
            if response.tool_calls:
                print("\n[Agent is fetching stock data...]\n")
                
                # Build the message history with proper ToolMessage objects
                conversation_history.append(response)
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    print(f"[DEBUG] Tool: {tool_name}, Args: {tool_args}")
                    
                    if tool_name in tools_map:
                        result = tools_map[tool_name].invoke(tool_args)
                        print(f"📊 {result}\n")
                        
                        # Add ToolMessage to conversation history
                        conversation_history.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call_id
                            )
                        )
                
                # Get final response from LLM with full conversation context
                final_response = llm_with_tools.invoke(conversation_history)
                
                # Add final response to history
                conversation_history.append(final_response)
                
                print(f"Bot: {final_response.content}\n")
            else:
                # Direct response without tool calls
                # Add the response to history
                conversation_history.append(response)
                
                print(f"Bot: {response.content}\n")
            
            # Show conversation length (for debugging)
            print(f"[History: {len(conversation_history)} messages total]")
            print()
                
        except Exception as e:
            print(f"❌ Error: {e}\n")
            import traceback
            traceback.print_exc()


# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    agent = create_agent()
    chat_with_agent(agent)