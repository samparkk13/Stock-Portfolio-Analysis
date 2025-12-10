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

# Load .env file from the config folder
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
load_dotenv(env_path)

# --- LANGCHAIN + OPENAI ---
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# --- IMPORT YOUR TOOLS ---
from src.tools.stock_tools import get_stock_price, get_multiple_stock_prices, get_portfolio_value, get_stock_volatility, get_stock_beta, get_portfolio_diversification, rebalance_equal_weight

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'my-chatbot-secret-key-2025')

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


# Initialize the agent globally
try:
    llm_with_tools = create_agent()
    tools_map = {
        "get_stock_price": fetch_stock_price,
        "get_multiple_stock_prices": fetch_multiple_stock_prices,
        "get_stock_volatility": fetch_stock_volatility,       
        "get_stock_beta": fetch_stock_beta,
        "get_portfolio_value": fetch_portfolio_value,
        "get_portfolio_diversification": fetch_portfolio_diversification,
        "rebalance_equal_weight": fetch_rebalance_equal_weight
    }
except Exception as e:
    print(f"Warning: Could not initialize agent: {e}")
    llm_with_tools = None
    tools_map = {}


@app.route('/')
def index():
    """Render the main chatbot page."""
    return render_template('index.html')

conversations = {}
portfolios = {}

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend."""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({
            'message': 'Please provide a message.',
            'status': 'error'
        }), 400
    
    if not llm_with_tools:
        return jsonify({
            'message': 'Chatbot is not properly configured. Please check your OPENAI_API_KEY.',
            'status': 'error'
        }), 500
    
    try:
        # --- SESSION MANAGEMENT ---
        # Get or create a unique conversation ID for this user's session
        if 'conversation_id' not in session:
            session['conversation_id'] = str(uuid.uuid4())
            print(f"[NEW SESSION] Created conversation ID: {session['conversation_id']}")
        
        conv_id = session['conversation_id']
        
        # Initialize conversation history if this is a new conversation
        if conv_id not in conversations:
            conversations[conv_id] = []
            print(f"[NEW CONVERSATION] Initialized history for {conv_id}")
    
        # Initialize portfolio storage if new
        if conv_id not in portfolios:
            portfolios[conv_id] = {}
        
        # Add user message to conversation history
        conversations[conv_id].append(HumanMessage(content=user_message))
        print(f"[HISTORY] Added user message. Total messages: {len(conversations[conv_id])}")

        # Invoke the LLM with the user's question
        response = llm_with_tools.invoke(conversations[conv_id])
        
        # Track tool calls for logging
        tool_logs = []
        
        # Check if the model wants to call a tool
        if response.tool_calls:
            # Build the message history with proper ToolMessage objects
            conversations[conv_id].append(response)
            
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                if tool_name in ["get_portfolio_value", "get_portfolio_diversification", "rebalance_equal_weight"]:
                    if "portfolio" not in tool_args or not tool_args["portfolio"]:
                        # Use stored portfolio if available
                        if portfolios[conv_id]:
                            tool_args["portfolio"] = portfolios[conv_id]
                            print(f"[PORTFOLIO] Injected stored portfolio: {portfolios[conv_id]}")
                        else:
                            # Fallback to example portfolio
                            tool_args["portfolio"] = {"VOO": 10, "AAPL": 20, "QQQ": 10}
                            print("[PORTFOLIO] No stored portfolio, using example")

                
                # Log tool call
                tool_logs.append({
                    'tool': tool_name,
                    'args': tool_args
                })
                
                if tool_name in tools_map:
                    result = tools_map[tool_name].invoke(tool_args)
                    tool_logs[-1]['result'] = str(result)

                    conversations[conv_id].append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call_id
                        )
                    )
            
            # Get final response from LLM with tool results
            final_response = llm_with_tools.invoke(conversations[conv_id])
            conversations[conv_id].append(final_response)
            bot_message = final_response.content
        else:
            # Direct response without tool calls
            # Add the response to history
            conversations[conv_id].append(response)

            # Direct response without tool calls
            bot_message = response.content
        
        return jsonify({
            'message': bot_message,
            'status': 'success',
            'tool_logs': tool_logs,
            'conversation_length': len(conversations[conv_id]),
            'has_portfolio': bool(portfolios.get(conv_id, {}))
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'message': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/set_portfolio', methods=['POST'])
def set_portfolio():
    """Store user's portfolio in session."""
    data = request.json
    portfolio = data.get('portfolio', {})
    
    if not portfolio:
        return jsonify({
            'message': 'No portfolio provided.',
            'status': 'error'
        }), 400
    
    # Get or create session
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    conv_id = session['conversation_id']
    
    # Store portfolio
    portfolios[conv_id] = portfolio
    
    # Add system message to conversation about portfolio setup
    if conv_id not in conversations:
        conversations[conv_id] = []
    
    portfolio_str = ", ".join([f"{shares} shares of {ticker}" for ticker, shares in portfolio.items()])
    
    conversations[conv_id].append(
        HumanMessage(content=f"My portfolio consists of: {portfolio_str}")
    )
    
    print(f"[PORTFOLIO] Stored portfolio for {conv_id}: {portfolio}")
    
    return jsonify({
        'message': 'Portfolio saved successfully!',
        'portfolio': portfolio,
        'status': 'success'
    })


@app.route('/get_portfolio', methods=['GET'])
def get_portfolio():
    """Retrieve user's stored portfolio."""
    if 'conversation_id' in session:
        conv_id = session['conversation_id']
        portfolio = portfolios.get(conv_id, {})
        
        return jsonify({
            'portfolio': portfolio,
            'has_portfolio': bool(portfolio),
            'status': 'success'
        })
    
    return jsonify({
        'portfolio': {},
        'has_portfolio': False,
        'status': 'info'
    })

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation history for the current session."""
    if 'conversation_id' in session:
        conv_id = session['conversation_id']
        if conv_id in conversations:
            del conversations[conv_id]
            print(f"[RESET] Cleared conversation history for {conv_id}")
        
        # Create new conversation ID
        session['conversation_id'] = str(uuid.uuid4())
        print(f"[RESET] New conversation ID: {session['conversation_id']}")
        
        return jsonify({
            'message': 'Conversation reset successfully.',
            'status': 'success'
        })
    
    return jsonify({
        'message': 'No active conversation to reset.',
        'status': 'info'
    })


@app.route('/history', methods=['GET'])
def get_history():
    """Get the current conversation history (for debugging)."""
    if 'conversation_id' in session:
        conv_id = session['conversation_id']
        if conv_id in conversations:
            history = []
            for msg in conversations[conv_id]:
                if isinstance(msg, HumanMessage):
                    history.append({'role': 'user', 'content': msg.content})
                elif isinstance(msg, AIMessage):
                    history.append({'role': 'assistant', 'content': msg.content})
                elif isinstance(msg, ToolMessage):
                    history.append({'role': 'tool', 'content': msg.content})
            
            return jsonify({
                'conversation_id': conv_id,
                'history': history,
                'message_count': len(conversations[conv_id])
            })
    
    return jsonify({
        'message': 'No conversation history found.',
        'status': 'info'
    })



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
