"""
Main entry point for the Stock Portfolio Chatbot (CLI).
WITH PORTFOLIO INPUT!
Integrates LangChain with custom financial tools in src/tools/stock_tools.py.
"""

import os
import sys
from typing import List, Dict

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
    Fetch the current real-time price of a given stock ticker symbol.
    Use when user asks about ONE specific stock's price.
    Example: 'AAPL', 'GOOGL', 'TSLA'
    """
    return get_stock_price(ticker)


@tool("get_multiple_stock_prices", return_direct=False)
def fetch_multiple_stock_prices(tickers: str) -> dict:
    """
    Fetch current prices for MULTIPLE ticker symbols at once.
    Use when user asks about several stocks together.
    Example: ['AAPL', 'GOOGL', 'MSFT']
    """
    if isinstance(tickers, str):
        # Clean and split user input safely
        tickers = [t.strip().upper() for t in tickers.replace("[", "").replace("]", "").replace("'", "").split(",")]
    return get_multiple_stock_prices(tickers)

@tool("get_stock_volatility", return_direct=False)
def fetch_stock_volatility(ticker: str) -> dict:
    """
    Calculate the annualized volatility (risk measure) of a stock.
    Use when user asks about risk, volatility, or how much a stock fluctuates.
    """
    return get_stock_volatility(ticker)


@tool("get_stock_beta", return_direct=False)
def fetch_stock_beta(ticker: str) -> dict:
    """
    Calculate beta (market correlation) of a stock vs the market (SPY).
    Use when user asks about beta, market correlation, or systematic risk.
    """
    return get_stock_beta(ticker)


@tool("get_portfolio_value", return_direct=False)
def fetch_portfolio_value(portfolio: dict) -> dict:
    """
    Calculate the total current market value of user's ENTIRE portfolio.
    Use when user asks: "What's my portfolio worth?", "Total value?", "Portfolio value?"
    Input format: {'AAPL': 10, 'GOOGL': 5} (ticker: shares)
    """
    return get_portfolio_value(portfolio)


@tool("get_portfolio_diversification", return_direct=False)
def fetch_portfolio_diversification(portfolio: dict) -> dict:
    """
    Analyze portfolio diversification across sectors.
    Use when user asks: "How diversified am I?", "Is my portfolio diversified?", "Sector concentration?"
    """
    return get_portfolio_diversification(portfolio)


@tool("rebalance_equal_weight", return_direct=False)
def fetch_rebalance_equal_weight(portfolio: dict) -> dict:
    """
    Suggest equal-weight rebalancing recommendations for portfolio.
    Use when user asks: "Should I rebalance?", "How to rebalance?", "Equal weight suggestions?"
    """
    return rebalance_equal_weight(portfolio)

# --- INITIALIZE AGENT ---

def create_agent():
    """Initializes the LangChain LLM with tools for stock analysis."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Set it in your environment or .env file.")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = [fetch_stock_price, fetch_multiple_stock_prices, fetch_stock_volatility,
    fetch_stock_beta,
    fetch_portfolio_value,
    fetch_portfolio_diversification,
    fetch_rebalance_equal_weight]
    
    # Bind tools to the LLM for function calling
    llm_with_tools = llm.bind_tools(tools)

    return llm_with_tools


# --- PORTFOLIO MANAGEMENT ---

def setup_portfolio() -> Dict[str, int]:
    """Interactive portfolio setup for CLI."""
    print("\n" + "="*60)
    print("📊 PORTFOLIO SETUP")
    print("="*60)
    print("\nLet's set up your portfolio for personalized analysis!")
    print("\nOptions:")
    print("  1. Enter your portfolio manually")
    print("  2. Use an example portfolio")
    print("  3. Skip for now")
    print()
    
    choice = input("Choose option (1/2/3): ").strip()
    
    if choice == "1":
        return setup_manual_portfolio()
    elif choice == "2":
        return setup_example_portfolio()
    else:
        print("\n✓ Skipped portfolio setup. You can add it later by typing 'portfolio'")
        return {}

def setup_manual_portfolio() -> Dict[str, int]:
    """Manually enter portfolio holdings."""
    portfolio = {}
    print("\n📝 Enter your holdings (type 'done' when finished)")
    print("Format: TICKER SHARES")
    print("Example: AAPL 10")
    print()
    
    while True:
        entry = input("  Add holding (or 'done'): ").strip()
        
        if entry.lower() == 'done':
            break
        
        try:
            parts = entry.split()
            if len(parts) != 2:
                print("  ❌ Format: TICKER SHARES (e.g., AAPL 10)")
                continue
            
            ticker = parts[0].upper()
            shares = int(parts[1])
            
            if shares <= 0:
                print("  ❌ Shares must be positive")
                continue
            
            portfolio[ticker] = shares
            print(f"  ✓ Added {shares} shares of {ticker}")
            
        except ValueError:
            print("  ❌ Invalid input. Format: TICKER SHARES")
    
    if portfolio:
        print(f"\n✓ Portfolio saved: {portfolio}")
    else:
        print("\n⚠️  No holdings added")
    
    return portfolio

def setup_example_portfolio() -> Dict[str, int]:
    """Choose from example portfolios."""
    examples = {
        '1': {
            'name': 'Conservative',
            'portfolio': {'VOO': 10, 'BND': 15, 'GLD': 5}
        },
        '2': {
            'name': 'Tech-Heavy',
            'portfolio': {'AAPL': 10, 'MSFT': 8, 'GOOGL': 5, 'NVDA': 6}
        },
        '3': {
            'name': 'Diversified',
            'portfolio': {'VOO': 10, 'QQQ': 8, 'VNQ': 5, 'BND': 7}
        }
    }
    
    print("\n📋 Example Portfolios:")
    for key, ex in examples.items():
        print(f"  {key}. {ex['name']}: {ex['portfolio']}")
    print()
    
    choice = input("Choose example (1/2/3): ").strip()
    
    if choice in examples:
        portfolio = examples[choice]['portfolio']
        print(f"\n✓ Using {examples[choice]['name']} portfolio: {portfolio}")
        return portfolio
    else:
        print("\n⚠️  Invalid choice, using empty portfolio")
        return {}

def display_portfolio(portfolio: Dict[str, int]):
    """Display current portfolio."""
    if not portfolio:
        print("\n📊 Portfolio: Not set")
        return
    
    print("\n📊 Current Portfolio:")
    for ticker, shares in portfolio.items():
        print(f"  • {ticker}: {shares} shares")

# --- CHAT LOOP ---

def chat_with_agent(llm_with_tools):
    """Runs an interactive chat loop in the terminal with portfolio support."""
    print("="*60)
    print("💬 StockBot is ready! Type 'exit' to quit.")
    print("="*60)
    print("✨ Features:")
    print("  • Conversation history enabled")
    print("  • Portfolio support for personalized analysis")
    print("  • Type 'portfolio' to view/edit your portfolio")
    print("  • Type 'reset' to clear conversation")
    print("="*60)
    print()
    print("Example queries:")
    print("  • What is the price of AAPL?")
    print("  • How volatile is TSLA?")
    print("  • What's my portfolio worth?")
    print("  • How diversified am I?")
    print("="*60)
    print()

    # Portfolio setup
    user_portfolio = setup_portfolio()

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
    
    # Add portfolio to conversation if set
    if user_portfolio:
        portfolio_str = ", ".join([f"{shares} shares of {ticker}" for ticker, shares in user_portfolio.items()])
        conversation_history.append(
            HumanMessage(content=f"My portfolio consists of: {portfolio_str}")
        )
    
    print("\n[SYSTEM] Ready! Conversation history initialized.\n")

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
            user_portfolio = {}
            print("\n[SYSTEM] ✅ Conversation and portfolio cleared. Starting fresh!\n")
            continue
        
        # Check for portfolio command
        if user_input.lower() == "portfolio":
            display_portfolio(user_portfolio)
            print("\nOptions:")
            print("  1. Edit portfolio")
            print("  2. Clear portfolio")
            print("  3. Back to chat")
            choice = input("Choose (1/2/3): ").strip()
            
            if choice == "1":
                user_portfolio = setup_portfolio()
            elif choice == "2":
                user_portfolio = {}
                print("✓ Portfolio cleared")
            print()
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
                print("\n[Agent is processing...]\n")
                
                # Add LLM response to history
                conversation_history.append(response)
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    # Inject portfolio if tool needs it
                    if tool_name in ["get_portfolio_value", "get_portfolio_diversification", "rebalance_equal_weight"]:
                        if "portfolio" not in tool_args or not tool_args["portfolio"]:
                            if user_portfolio:
                                tool_args["portfolio"] = user_portfolio
                                print(f"[DEBUG] Using stored portfolio: {user_portfolio}")
                            else:
                                print(f"[WARNING] No portfolio set! Using example portfolio.")
                                tool_args["portfolio"] = {"VOO": 10, "AAPL": 20, "QQQ": 10}
                    
                    print(f"[DEBUG] Tool: {tool_name}, Args: {tool_args}")
                    
                    if tool_name in tools_map:
                        result = tools_map[tool_name].invoke(tool_args)
                        print(f"📊 Result: {result}\n")
                        
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
    print("\n🚀 Starting Stock Portfolio Chatbot (CLI with Portfolio Support)\n")
    agent = create_agent()
    chat_with_agent(agent)