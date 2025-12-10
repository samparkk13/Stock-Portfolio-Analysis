// Chat functionality with portfolio input
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const logContent = document.getElementById('logContent');
const clearLogButton = document.getElementById('clearLogButton');

// Portfolio modal elements
const portfolioModal = document.getElementById('portfolioModal');
const portfolioHoldings = document.getElementById('portfolioHoldings');
const tickerInput = document.getElementById('tickerInput');
const sharesInput = document.getElementById('sharesInput');
const addHoldingBtn = document.getElementById('addHoldingBtn');
const savePortfolioBtn = document.getElementById('savePortfolioBtn');
const skipPortfolioBtn = document.getElementById('skipPortfolioBtn');
const editPortfolioBtn = document.getElementById('editPortfolioBtn');
const portfolioStatus = document.getElementById('portfolioStatus');

// Store portfolio locally
let userPortfolio = {};

// Example portfolios
const examplePortfolios = {
    conservative: {
        'VOO': 10,  // S&P 500 ETF
        'BND': 15,  // Bond ETF
        'GLD': 5    // Gold ETF
    },
    tech: {
        'AAPL': 10,
        'MSFT': 8,
        'GOOGL': 5,
        'NVDA': 6
    },
    diversified: {
        'VOO': 10,   // S&P 500
        'QQQ': 8,    // NASDAQ
        'VNQ': 5,    // Real Estate
        'BND': 7     // Bonds
    }
};

// Show portfolio modal on first load
window.addEventListener('load', () => {
    checkPortfolio();
});

function checkPortfolio() {
    // Check if user has portfolio
    fetch('/get_portfolio')
        .then(response => response.json())
        .then(data => {
            if (data.has_portfolio && Object.keys(data.portfolio).length > 0) {
                userPortfolio = data.portfolio;
                updatePortfolioStatus();
            } else {
                // Show modal on first visit
                portfolioModal.style.display = 'flex';
            }
        });
}

function updatePortfolioStatus() {
    const holdings = Object.keys(userPortfolio).length;
    if (holdings > 0) {
        const summary = Object.entries(userPortfolio)
            .map(([ticker, shares]) => `${shares} ${ticker}`)
            .join(', ');
        portfolioStatus.textContent = `Portfolio: ${summary}`;
    } else {
        portfolioStatus.textContent = 'No portfolio set';
    }
}

function renderPortfolioHoldings() {
    portfolioHoldings.innerHTML = '';
    
    if (Object.keys(userPortfolio).length === 0) {
        portfolioHoldings.innerHTML = '<p class="no-holdings">No holdings yet. Add some stocks below!</p>';
        return;
    }
    
    for (const [ticker, shares] of Object.entries(userPortfolio)) {
        const holdingDiv = document.createElement('div');
        holdingDiv.className = 'holding-item';
        holdingDiv.innerHTML = `
            <span class="holding-ticker">${ticker}</span>
            <span class="holding-shares">${shares} shares</span>
            <button class="remove-btn" onclick="removeHolding('${ticker}')">×</button>
        `;
        portfolioHoldings.appendChild(holdingDiv);
    }
}

function addHolding() {
    const ticker = tickerInput.value.trim().toUpperCase();
    const shares = parseInt(sharesInput.value);
    
    if (!ticker || !shares || shares <= 0) {
        alert('Please enter a valid ticker and number of shares');
        return;
    }
    
    userPortfolio[ticker] = shares;
    renderPortfolioHoldings();
    
    // Clear inputs
    tickerInput.value = '';
    sharesInput.value = '';
    tickerInput.focus();
}

function removeHolding(ticker) {
    delete userPortfolio[ticker];
    renderPortfolioHoldings();
}

function savePortfolio() {
    if (Object.keys(userPortfolio).length === 0) {
        alert('Please add at least one holding to your portfolio');
        return;
    }
    
    // Save to backend
    fetch('/set_portfolio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio: userPortfolio })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Close modal
            portfolioModal.style.display = 'none';
            updatePortfolioStatus();
            
            // Add welcome message with portfolio summary
            const holdingsList = Object.entries(userPortfolio)
                .map(([ticker, shares]) => `${shares} shares of ${ticker}`)
                .join(', ');
            
            addMessage(`Perfect! I've recorded your portfolio: ${holdingsList}. How can I help you analyze it?`, 'bot');
        }
    })
    .catch(error => {
        console.error('Error saving portfolio:', error);
        alert('Failed to save portfolio. Please try again.');
    });
}

function skipPortfolio() {
    portfolioModal.style.display = 'none';
    addMessage("No problem! You can add your portfolio later by clicking the edit button in the header. In the meantime, feel free to ask me about any stocks or portfolios!", 'bot');
}

// Event listeners for portfolio modal
addHoldingBtn.addEventListener('click', addHolding);
savePortfolioBtn.addEventListener('click', savePortfolio);
skipPortfolioBtn.addEventListener('click', skipPortfolio);
editPortfolioBtn.addEventListener('click', () => {
    renderPortfolioHoldings();
    portfolioModal.style.display = 'flex';
});

// Allow Enter key to add holding
tickerInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (tickerInput.value.trim()) {
            sharesInput.focus();
        }
    }
});

sharesInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        addHolding();
    }
});

// Example portfolio buttons
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const example = btn.dataset.example;
        userPortfolio = {...examplePortfolios[example]};
        renderPortfolioHoldings();
    });
});

// Auto-resize textarea
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Send message on Enter (Shift+Enter for new line)
chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Send button click handler
sendButton.addEventListener('click', sendMessage);

// Clear log button handler
clearLogButton.addEventListener('click', clearLog);

function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Disable input while processing
    setInputState(false);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Track start time
    const startTime = Date.now();
    
    // Send message to backend
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Calculate response time
        const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        if (data.status === 'success') {
            addMessage(data.message, 'bot', responseTime);
            
            // Add tool logs if any
            if (data.tool_logs && data.tool_logs.length > 0) {
                data.tool_logs.forEach(log => {
                    addToolLog(log);
                });
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot', responseTime);
        }
        
        // Re-enable input
        setInputState(true);
    })
    .catch(error => {
        console.error('Error:', error);
        const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
        removeTypingIndicator();
        addMessage('Sorry, I encountered an error connecting to the server.', 'bot', responseTime);
        setInputState(true);
    });
}

function addMessage(text, type, responseTime = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    // Add appropriate icon
    if (type === 'bot') {
        avatarDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 8V4H8"/>
                <rect width="16" height="12" x="4" y="8" rx="2"/>
                <path d="M2 14h2"/>
                <path d="M20 14h2"/>
                <path d="M15 13v2"/>
                <path d="M9 13v2"/>
            </svg>
        `;
    } else {
        avatarDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        `;
    }
    
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-wrapper';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Render markdown for bot messages, escape HTML for user messages
    if (type === 'bot') {
        contentDiv.innerHTML = marked.parse(text);
    } else {
        contentDiv.innerHTML = `<p>${escapeHtml(text)}</p>`;
    }
    
    contentWrapper.appendChild(contentDiv);
    
    // Add response time for bot messages if provided
    if (type === 'bot' && responseTime !== null) {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'response-time';
        timeDiv.textContent = `${responseTime}s`;
        contentWrapper.appendChild(timeDiv);
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentWrapper);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 8V4H8"/>
                <rect width="16" height="12" x="4" y="8" rx="2"/>
                <path d="M2 14h2"/>
                <path d="M20 14h2"/>
                <path d="M15 13v2"/>
                <path d="M9 13v2"/>
            </svg>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function setInputState(enabled) {
    chatInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    if (enabled) {
        chatInput.focus();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addToolLog(log) {
    // Remove empty state if present
    const emptyState = logContent.querySelector('.log-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const timestamp = new Date().toLocaleTimeString();
    
    let logHTML = `
        <div class="log-timestamp">${timestamp}</div>
        <div class="log-tool">
            <span class="log-label">Tool:</span> ${escapeHtml(log.tool)}
        </div>
    `;
    
    if (log.args) {
        logHTML += `
            <div class="log-args">
                <span class="log-label">Args:</span> ${escapeHtml(JSON.stringify(log.args, null, 2))}
            </div>
        `;
    }
    
    if (log.result) {
        logHTML += `
            <div class="log-result">
                <span class="log-label">Result:</span><br>${escapeHtml(log.result)}
            </div>
        `;
    }
    
    logEntry.innerHTML = logHTML;
    logContent.appendChild(logEntry);
    
    // Scroll to bottom of log
    logContent.scrollTop = logContent.scrollHeight;
}

function clearLog() {
    logContent.innerHTML = `
        <div class="log-empty">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <p>No tool calls yet</p>
        </div>
    `;
}

// Focus input on load (after checking portfolio)
window.addEventListener('load', () => {
    setTimeout(() => {
        chatInput.focus();
    }, 500);
});