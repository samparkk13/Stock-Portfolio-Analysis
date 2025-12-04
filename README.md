# Stock Portfolio Analysis Chatbot 📈💬

AI-powered financial portfolio analysis through natural conversation. Built with GPT-4, LangChain, and Flask.

**Team Members:**
- Lucas Guillet (lkg49)
- Chris Johnson (crj36)
- Sam Park (sp994)

---

## 📖 Project Overview

This project develops an AI-powered chatbot that provides personalized portfolio analysis and risk management through natural language conversations. Unlike traditional financial platforms that rely on complex dashboards, our chatbot enables users to ask questions like:

- "What is the stock price of AAPL?"
- "Is my portfolio too risky for my goals?"
- "How would rising interest rates affect my investments?"

The system combines **GPT-4's natural language understanding** with **deterministic Python-based financial calculation tools**, ensuring both conversational fluidity and computational accuracy.

### Key Features

✅ **Natural Language Interface** - Ask questions in plain English  
✅ **Real-Time Market Data** - Fetches current stock prices via Yahoo Finance API  
✅ **Hybrid Architecture** - LLM for conversation + Python tools for accuracy  
✅ **Tool Calling** - Automatically selects and executes appropriate financial tools  
✅ **Dual Interface** - CLI for testing, Web UI for production  
✅ **Transparent Execution** - See exactly what tools are being called and why

---

### Technology Stack

- **Language Model:** OpenAI GPT-4
- **Framework:** LangChain (tool orchestration)
- **Market Data:** Yahoo Finance API (yfinance)
- **Backend:** Python 3.x
- **Web Framework:** Flask
- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **Libraries:** pandas, numpy, python-dotenv

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd portfolio-analysis-chatbot
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `langchain`
- `langchain-openai`
- `openai`
- `python-dotenv`
- `yfinance`
- `pandas`
- `numpy`
- `flask` (for web interface)

### Step 4: Configure API Key

Create a `.env` file in the `config/` directory:

```bash
# config/.env
OPENAI_API_KEY=your_openai_api_key_here
```

⚠️ **Important:** Never commit your `.env` file to version control. It should be in `.gitignore`.

---

## 💻 How to Run

### Option 1: CLI (Command-Line Interface)

Best for testing and debugging.

```bash
# From project root directory
python app/main.py
```

**Example usage:**
```
💬 StockBot is ready! Type 'exit' to quit.

Ask me about stock prices! Example: 'What is the price of AAPL?'

You: What is the stock price of AAPL?

[Agent is fetching stock data...]

[DEBUG] Tool: get_stock_price, Args: {'ticker': 'AAPL'}
📊 {'ticker': 'AAPL', 'price': 275.61, ...}

Bot: The current stock price of AAPL (Apple Inc.) is $275.61 USD.

You: exit
Goodbye!
```

### Option 2: Web Interface (Recommended)

User-friendly web interface.

```bash
# From project root directory
python app/web_app.py
```

Then open your browser and navigate to:
```
http://localhost:5001
```

---

## 📚 References & Related Work

1. Lee, J., Stevens, N., & Han, S. C. (2025). Large Language Models in Finance (FinLLMs). *Neural Computing and Applications*, 37(30), 24853–24867.

2. IBM Think. (2024). [What is LangChain?](https://www.ibm.com/think/topics/langchain)

3. IBM Think. (2024). [What is RAG?](https://www.ibm.com/think/topics/retrieval-augmented-generation)

4. LangChain Documentation. (2024). [Python Documentation](https://python.langchain.com/docs/)

5. OpenAI. (2024). [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

---

## 📄 License

This project is developed as part of CS 4701 coursework at Cornell University.

---

- LangChain community for documentation and examples

---

**Built with ❤️ at Cornell University**

*Last Updated: December 2025*