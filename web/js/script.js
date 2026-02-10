document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChat');
    const themeToggle = document.getElementById('themeToggle');
    const voiceToggle = document.getElementById('voiceToggle');
    const quickActionBtns = document.querySelectorAll('.action-btn');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    const typingIndicator = document.getElementById('typingIndicator');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const helpModal = document.getElementById('helpModal');
    const helpBtn = document.getElementById('helpBtn');
    const closeHelp = document.getElementById('closeHelp');
    
    // State
    let currentTheme = localStorage.getItem('theme') || 'light';
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    
    // Initialize
    initTheme();
    loadChatHistory();
    
    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    clearChatBtn.addEventListener('click', clearChat);
    themeToggle.addEventListener('click', toggleTheme);
    helpBtn.addEventListener('click', () => showModal(helpModal));
    closeHelp.addEventListener('click', () => hideModal(helpModal));
    
    // Quick Actions
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            messageInput.value = prompt;
            messageInput.focus();
        });
    });
    
    // Suggestions
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            addMessage(prompt, 'user');
            simulateAIResponse(prompt);
        });
    });
    
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Voice Toggle
    voiceToggle.addEventListener('change', function() {
        if (this.checked) {
            showNotification('Voice response enabled', 'success');
            initVoiceRecognition();
        } else {
            showNotification('Voice response disabled', 'info');
        }
    });
    
    // Functions
    function initTheme() {
        document.documentElement.setAttribute('data-theme', currentTheme);
        updateThemeButton();
    }
    
    function toggleTheme() {
        currentTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        localStorage.setItem('theme', currentTheme);
        updateThemeButton();
        showNotification(`Switched to ${currentTheme} theme`, 'info');
    }
    
    function updateThemeButton() {
        const icon = themeToggle.querySelector('i');
        const text = themeToggle.querySelector('span');
        
        if (currentTheme === 'dark') {
            icon.className = 'fas fa-sun';
            text.textContent = 'Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            text.textContent = 'Dark Mode';
        }
    }
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        addMessage(message, 'user');
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Hide welcome message
        if (welcomeMessage.style.display !== 'none') {
            welcomeMessage.style.display = 'none';
        }
        
        // Simulate AI response
        simulateAIResponse(message);
        
        // Save to history
        saveChatHistory();
    }
    
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${formatMessage(text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function formatMessage(text) {
        // Simple markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    function simulateAIResponse(userMessage) {
        // Show typing indicator
        typingIndicator.style.display = 'flex';
        
        // Simulate thinking time based on message length
        const thinkingTime = Math.min(userMessage.length * 50, 3000);
        
        setTimeout(() => {
            typingIndicator.style.display = 'none';
            
            // Generate AI response based on user message
            const response = generateAIResponse(userMessage);
            addMessage(response, 'ai');
            
            // Update analytics
            updateAnalytics();
            
            // Save to history
            saveChatHistory();
        }, thinkingTime);
    }
    
    function generateAIResponse(userMessage) {
        const responses = {
            'project': "I can help with project planning! Here's a suggested structure:\n\n1. **Define Requirements** - List all features and specifications\n2. **Create Timeline** - Break down tasks with deadlines\n3. **Tech Stack** - Choose appropriate technologies\n4. **MVP Planning** - Identify minimum viable product features\n5. **Testing Strategy** - Plan for quality assurance\n\nWould you like me to elaborate on any of these points?",
            'code': "I'd be happy to help with coding! Here's a Python function template:\n\n```python\ndef function_name(parameters):\n    \"\"\"Docstring explaining the function\"\"\"\n    # Implementation here\n    result = process_data(parameters)\n    return result\n```\n\nWhat specific functionality are you looking to implement?",
            'debug': "For debugging, try these steps:\n\n1. **Reproduce the Error** - Make sure you can consistently reproduce it\n2. **Check Error Message** - Read the complete error traceback\n3. **Isolate the Issue** - Test components separately\n4. **Check Documentation** - Verify correct usage\n5. **Search Online** - Others might have solved similar issues\n\nWhat specific error are you encountering?",
            'default': "Thank you for your message! I'm an AI assistant specialized in project management and development. I can help you with:\n\n• Project planning and timelines\n• Code generation and optimization\n• Debugging assistance\n• Technical explanations\n• Resource recommendations\n\nHow can I assist you further with your project?"
        };
        
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('project') || lowerMessage.includes('plan')) {
            return responses.project;
        } else if (lowerMessage.includes('code') || lowerMessage.includes('function')) {
            return responses.code;
        } else if (lowerMessage.includes('debug') || lowerMessage.includes('error')) {
            return responses.debug;
        } else {
            return responses.default;
        }
    }
    
    function clearChat() {
        if (confirm('Are you sure you want to clear all chat messages?')) {
            chatMessages.innerHTML = '';
            chatHistory = [];
            localStorage.removeItem('chatHistory');
            welcomeMessage.style.display = 'block';
            showNotification('Chat cleared', 'success');
        }
    }
    
    function loadChatHistory() {
        if (chatHistory.length > 0) {
            welcomeMessage.style.display = 'none';
            chatHistory.forEach(msg => {
                addMessage(msg.text, msg.sender);
            });
        }
    }
    
    function saveChatHistory() {
        const messages = [];
        document.querySelectorAll('.message').forEach(msg => {
            const sender = msg.classList.contains('user') ? 'user' : 'ai';
            const text = msg.querySelector('.message-text').textContent;
            messages.push({ sender, text });
        });
        
        // Keep only last 50 messages to prevent localStorage overflow
        chatHistory = messages.slice(-50);
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }
    
    function updateAnalytics() {
        // Update today's chats count
        const todayChats = document.getElementById('todayChats');
        let count = parseInt(todayChats.textContent);
        todayChats.textContent = count + 1;
        
        // Update tasks created (random for demo)
        const tasksCreated = document.getElementById('tasksCreated');
        if (Math.random() > 0.7) {
            let tasks = parseInt(tasksCreated.textContent);
            tasksCreated.textContent = tasks + 1;
        }
    }
    
    function initVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            showNotification('Voice recognition ready. Click microphone button to start.', 'info');
        } else {
            showNotification('Voice recognition not supported in your browser', 'warning');
            voiceToggle.checked = false;
        }
    }
    
    function showModal(modal) {
        modal.style.display = 'flex';
    }
    
    function hideModal(modal) {
        modal.style.display = 'none';
    }
    
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to body
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Add notification styles
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--surface-color);
            color: var(--text-primary);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            z-index: 1001;
            transform: translateX(150%);
            transition: transform 0.3s ease;
            border-left: 4px solid var(--primary-color);
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-success {
            border-left-color: var(--success-color);
        }
        
        .notification-info {
            border-left-color: var(--primary-color);
        }
        
        .notification-warning {
            border-left-color: var(--warning-color);
        }
        
        .notification i {
            font-size: 1.2rem;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize with a welcome message
    setTimeout(() => {
        if (chatHistory.length === 0) {
            showNotification('Welcome to AI Project Assistant! Try asking me anything about your project.', 'info');
        }
    }, 1000);
});
