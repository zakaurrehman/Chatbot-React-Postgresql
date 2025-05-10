import React, { useEffect } from 'react';
import { marked } from 'marked';
import './home.css';

const Home = () => {
  useEffect(() => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const clearChatBtn = document.getElementById('clear-chat');

    // Set up marked options for markdown parsing
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false
    });

    loadChatHistory();

    function getCurrentTime() {
      const now = new Date();
      return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Modified to ensure full message is displayed
    function addMessage(message, isUser = false) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

      if (isUser) {
        messageDiv.textContent = message;
      } else {
        // Ensure message is a string before parsing
        const messageStr = typeof message === 'string' ? message : String(message);
        // Parse markdown and set HTML content
        messageDiv.innerHTML = marked.parse(messageStr);
        addProgressBars(messageDiv);
      }

      const timeDiv = document.createElement('div');
      timeDiv.className = 'message-time';
      timeDiv.textContent = getCurrentTime();

      const messageContainer = document.createElement('div');
      messageContainer.className = 'mb-3';
      messageContainer.appendChild(messageDiv);
      messageContainer.appendChild(timeDiv);

      chatMessages.appendChild(messageContainer);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      saveChatHistory();
    }

    function addProgressBars(messageDiv) {
      const progressRegex = /(\d+(\.\d+)?)%\s*(complete|progress)/gi;
      const html = messageDiv.innerHTML;
      const newHtml = html.replace(progressRegex, (match, percentage) => {
        const numPercentage = parseFloat(percentage);
        return `${match} 
        <div class="progress-indicator">
          <div class="progress-bar" style="width: ${numPercentage}%"></div>
        </div>`;
      });

      messageDiv.innerHTML = newHtml;
    }

    function addChart(chartUrl) {
      const chartDiv = document.createElement('div');
      chartDiv.className = 'chart-container';

      const chartImg = document.createElement('img');
      chartImg.src = chartUrl;
      chartImg.alt = 'Chart';
      chartImg.loading = 'lazy';

      chartDiv.appendChild(chartImg);
      chatMessages.appendChild(chartDiv);

      chatMessages.scrollTop = chatMessages.scrollHeight;
      saveChatHistory();
    }

    function showLoading() {
      const loadingDiv = document.createElement('div');
      loadingDiv.className = 'message bot-message loading-message';
      loadingDiv.id = 'loading-message';

      const loadingIndicator = document.createElement('div');
      loadingIndicator.className = 'loading';

      loadingDiv.appendChild(loadingIndicator);
      chatMessages.appendChild(loadingDiv);

      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideLoading() {
      const loadingMessage = document.getElementById('loading-message');
      if (loadingMessage) {
        loadingMessage.remove();
      }
    }

    window.askQuestion = (question) => {
      userInput.value = question;
      chatForm.dispatchEvent(new Event('submit'));
    };

    function saveChatHistory() {
      const chatHistory = chatMessages.innerHTML;
      localStorage.setItem('chatHistory', chatHistory);
    }

    function loadChatHistory() {
      const chatHistory = localStorage.getItem('chatHistory');
      if (chatHistory) {
        chatMessages.innerHTML = chatHistory;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }

    function clearChat() {
      if (window.confirm('Are you sure you want to clear the chat history?')) {
        localStorage.removeItem('chatHistory');
        chatMessages.innerHTML = `
          <div class="message bot-message">
            <div>👋 Welcome to the Construction Project Management Assistant. How can I help you today?</div>
          </div>
          
          <div class="mt-3 mb-4">
            <div class="suggestions-label">Here are some questions you can ask:</div>
            <button class="btn btn-sm suggestion-btn" onclick="askQuestion('Show me all active projects')">
              <i class="bi bi-list-check"></i> Show active projects
            </button>
            <button class="btn btn-sm suggestion-btn" onclick="askQuestion('What is the status of JAIN-1B project?')">
              <i class="bi bi-info-circle"></i> Project status
            </button>
            <button class="btn btn-sm suggestion-btn" onclick="askQuestion('Show me progress of ELMGROVE-1B')">
              <i class="bi bi-graph-up"></i> Project progress
            </button>
            <button class="btn btn-sm suggestion-btn" onclick="askQuestion('Show me the details of CABOT-1B project')">
              <i class="bi bi-file-earmark-text"></i> Project details
            </button>
          </div>
        `;
      }
    }

    // Modified to ensure full response is received and displayed
    chatForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      const message = userInput.value.trim();
      if (!message) return;

      addMessage(message, true);
      userInput.value = '';
      showLoading();

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });

        if (!response.ok) throw new Error('Server error');
        
        const data = await response.json();
        console.log('Response received:', data); // Debug logging

        hideLoading();
        
        // Make sure we're getting the full response
        if (data && data.message) {
          addMessage(data.message);
        } else {
          addMessage("I received a response but couldn't display it properly. Please try again.");
        }
        
        if (data && data.chart) {
          addChart(data.chart);
        }

      } catch (error) {
        hideLoading();
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error while processing your request. Please try again.', false);
      }
    });

    clearChatBtn.addEventListener('click', clearChat);

    userInput.addEventListener('keydown', function (e) {
      if (e.ctrlKey && e.key === 'Enter') {
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    window.addEventListener('load', function () {
      userInput.focus();
    });

  }, []);

  const inputStyle = {
    borderRadius: '20px 0 0 20px',
    border: '1px solid #444',
    backgroundColor: '#333',
    color: '#e0e0e0',
    height: '48px',
    padding: '0 15px',
    fontSize: '1rem',
    flex: 1,
    outline: 'none'
  };
  
  const buttonStyle = {
    borderRadius: '0 20px 20px 0',
    background: 'linear-gradient(135deg, #2563eb, #1e40af)',
    border: 'none',
    height: '48px',
    width: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0,
    color: '#fff'
  };
  
  const iconStyle = {
    fontSize: '1.2rem'
  };

  const chatHeaderStyle = {
    padding: '15px 20px',
    background: 'linear-gradient(135deg, #2563eb, #1e40af)',
    color: 'white',
    borderTopLeftRadius: '10px',
    borderTopRightRadius: '10px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };
  
  const titleStyle = {
    margin: 0,
    fontSize: '1.25rem',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  };
  
  const clearButtonStyle = {
    border: '1px solid white',
    borderRadius: '8px',
    background: 'transparent',
    color: 'white',
    padding: '4px 8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '32px',
    width: '32px'
  };
  
  const iconStyl = {
    fontSize: '1.2rem'
  };
  
  return (
    <div className="container mt-4 mb-4">
      <div className="chat-container">
        <div style={chatHeaderStyle}>
          <h4 style={titleStyle}>
            <i className="bi bi-building" style={iconStyle}></i> Construction Project Management Assistant
          </h4>
          <button id="clear-chat" title="Clear Chat" style={clearButtonStyle}>
            <i className="bi bi-trash" style={iconStyl}></i>
          </button>
        </div>

        <div className="chat-messages" id="chat-messages">
          <div className="message bot-message">
            <div><span role="img" aria-label="celebration">🎉</span> Welcome to the Construction Project Management Assistant. How can I help you today?</div>
          </div>

          <div className="mt-3 mb-4">
            <div className="suggestions-label">Here are some questions you can ask:</div>
            <button className="btn btn-sm suggestion-btn" onClick={() => window.askQuestion('Show me all active projects')}>
              <i className="bi bi-list-check"></i> Show active projects
            </button>
            <button className="btn btn-sm suggestion-btn" onClick={() => window.askQuestion('What is the status of JAIN-1B project?')}>
              <i className="bi bi-info-circle"></i> Project status
            </button>
            <button className="btn btn-sm suggestion-btn" onClick={() => window.askQuestion('Show me progress of ELMGROVE-1B')}>
              <i className="bi bi-graph-up"></i> Project progress
            </button>
            <button className="btn btn-sm suggestion-btn" onClick={() => window.askQuestion('Show me the details of CABOT-1B project')}>
              <i className="bi bi-file-earmark-text"></i> Project details
            </button>
          </div>
        </div>

        <div className="chat-input">
          <form id="chat-form">
            <div className="input-group" style={{ display: 'flex' }}>
              <input
                type="text"
                id="user-input"
                className="form-control"
                placeholder="Type your message here..."
                autoComplete="off"
                style={inputStyle}
              />
              <button type="submit" className="btn btn-primary" style={buttonStyle}>
                <i className="bi bi-send" style={iconStyle}></i>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Home;