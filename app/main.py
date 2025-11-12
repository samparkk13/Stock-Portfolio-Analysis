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
from src.tools.stock_tools import get_stock_price, get_multiple_stock_prices


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


# --- INITIALIZE AGENT ---

def create_agent():
    """Initializes the LangChain LLM with tools for stock analysis."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Set it in your environment or .env file.")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = [fetch_stock_price, fetch_multiple_stock_prices]
    
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
        "get_multiple_stock_prices": fetch_multiple_stock_prices
    }

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        try:
            # Invoke the LLM with the user's question
            response = llm_with_tools.invoke([HumanMessage(content=user_input)])
            
            # Check if the model wants to call a tool
            if response.tool_calls:
                print("\n[Agent is fetching stock data...]\n")
                
                # Build the message history with proper ToolMessage objects
                messages = [HumanMessage(content=user_input), response]
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    print(f"[DEBUG] Tool: {tool_name}, Args: {tool_args}")
                    
                    if tool_name in tools_map:
                        result = tools_map[tool_name].invoke(tool_args)
                        print(f"📊 {result}\n")
                        
                        # Add ToolMessage with the result and matching tool_call_id
                        messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call_id
                            )
                        )
                
                # Get final response from LLM with tool results
                final_response = llm_with_tools.invoke(messages)
                print(f"Bot: {final_response.content}\n")
            else:
                # Direct response without tool calls
                print(f"Bot: {response.content}\n")
                
        except Exception as e:
            print(f"❌ Error: {e}\n")
            import traceback
            traceback.print_exc()


# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    agent = create_agent()
    chat_with_agent(agent)