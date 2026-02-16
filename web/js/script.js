document.addEventListener('DOMContentLoaded', () => {
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
    const attachBtn = document.getElementById('attachBtn');
    const fileInput = document.getElementById('fileInput');
    const voiceBtn = document.getElementById('voiceBtn');
    const exportChatBtn = document.getElementById('exportChat');
    const viewHistoryBtn = document.getElementById('viewHistory');
    const companyMode = document.getElementById('companyMode');
    const speechLanguage = document.getElementById('speechLanguage');
    const marketBannerText = document.getElementById('marketBannerText');
    const responseSpeed = document.getElementById('responseSpeed');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    let currentTheme = localStorage.getItem('theme') || 'light';
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    let attachedFiles = [];
    let recognition = null;
    let isRecording = false;
    let selectedCompanyMode = localStorage.getItem('companyMode') || 'smb';
    let selectedSpeechLanguage = localStorage.getItem('speechLanguage') || 'en-US';

    const companyProfiles = {
        startup: {
            label: 'Startup',
            banner: 'Startup demo mode active: fast MVP, lower cost, fast iteration roadmap.',
            style: 'Prioritize speed, lean architecture, and measurable MVP outcomes.'
        },
        smb: {
            label: 'SMB',
            banner: 'SMB demo mode active: practical delivery, pricing-friendly recommendations.',
            style: 'Focus on quick deployment, budget-fit decisions, and easy team adoption.'
        },
        enterprise: {
            label: 'Enterprise',
            banner: 'Enterprise demo mode active: governance, security, and scale-ready design.',
            style: 'Emphasize compliance, role-based access, integration, and reliability.'
        },
        agency: {
            label: 'Agency',
            banner: 'Agency demo mode active: client reporting, multi-project workflow, and handoff.',
            style: 'Highlight repeatable delivery, client transparency, and service packaging.'
        }
    };

    initTheme();
    initSavedPreferences();
    loadChatHistory();
    initSpeechRecognition();

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${messageInput.scrollHeight}px`;
    });

    clearChatBtn.addEventListener('click', clearChat);
    themeToggle.addEventListener('click', toggleTheme);
    helpBtn.addEventListener('click', () => showModal(helpModal));
    closeHelp.addEventListener('click', () => hideModal(helpModal));

    attachBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    voiceBtn.addEventListener('click', toggleVoiceInput);
    exportChatBtn.addEventListener('click', exportChat);
    viewHistoryBtn.addEventListener('click', showHistorySnapshot);
    companyMode.addEventListener('change', updateCompanyMode);
    speechLanguage.addEventListener('change', updateSpeechLanguage);

    voiceToggle.addEventListener('change', function () {
        const msg = this.checked ? 'Voice response enabled' : 'Voice response disabled';
        showNotification(msg, this.checked ? 'success' : 'info');
    });

    quickActionBtns.forEach((btn) => {
        btn.addEventListener('click', function () {
            const prompt = this.getAttribute('data-prompt');
            messageInput.value = prompt;
            messageInput.focus();
        });
    });

    suggestionBtns.forEach((btn) => {
        btn.addEventListener('click', function () {
            messageInput.value = this.getAttribute('data-prompt');
            sendMessage();
        });
    });

    function initSavedPreferences() {
        companyMode.value = selectedCompanyMode;
        speechLanguage.value = selectedSpeechLanguage;
        applyCompanyBanner(selectedCompanyMode);
    }

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
            return;
        }
        icon.className = 'fas fa-moon';
        text.textContent = 'Dark Mode';
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        messageInput.value = '';
        messageInput.style.height = 'auto';

        if (welcomeMessage.style.display !== 'none') {
            welcomeMessage.style.display = 'none';
        }

        simulateAIResponse(message);
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

    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatMessage(text) {
        const safe = escapeHtml(text);
        return safe
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    function simulateAIResponse(userMessage) {
        typingIndicator.style.display = 'flex';

        const speedMap = { fast: 20, normal: 45, slow: 70 };
        const charWeight = speedMap[responseSpeed.value] || speedMap.normal;
        const thinkingTime = Math.min(Math.max(userMessage.length * charWeight, 500), 4500);

        setTimeout(() => {
            typingIndicator.style.display = 'none';
            const response = generateAIResponse(userMessage);
            addMessage(response, 'ai');
            updateAnalytics();
            saveChatHistory();
            speakIfEnabled(response);
        }, thinkingTime);
    }

    function generateAIResponse(userMessage) {
        const profile = companyProfiles[selectedCompanyMode] || companyProfiles.smb;
        const lower = userMessage.toLowerCase();

        const fileContext = attachedFiles.length
            ? `\n\nFile context loaded (${attachedFiles.length}): ${attachedFiles.map((f) => f.name).join(', ')}.`
            : '';

        if (lower.includes('proposal') || lower.includes('company') || lower.includes('sell')) {
            return [
                `Here is a ${profile.label}-focused market pitch:`,
                '',
                '1. **Problem**: Teams lose time across scattered chat, files, and meetings.',
                '2. **Solution**: This assistant combines chat, voice input, and file analysis in one workspace.',
                '3. **Business Value**: Faster decisions, less manual reporting, improved team productivity.',
                `4. **Delivery Style**: ${profile.style}`,
                '5. **Offer Structure**: Setup + monthly support + optional custom integrations.',
                fileContext
            ].join('\n');
        }

        if (lower.includes('file') || lower.includes('document') || lower.includes('analy')) {
            if (!attachedFiles.length) {
                return 'Please attach a file first, then ask for analysis. I can summarize content, risks, and next actions.';
            }
            const snippets = attachedFiles
                .slice(0, 2)
                .map((f) => `- **${f.name}**: ${truncateText(f.content, 220)}`)
                .join('\n');
            return [
                `I reviewed your uploaded file content for ${profile.label} usage.`,
                '',
                '**Summary**',
                snippets,
                '',
                '**Business Risks**',
                '- Missing process ownership can delay rollouts.',
                '- Unclear KPIs reduce executive confidence.',
                '',
                '**Next Actions**',
                '- Define owner, timeline, and measurable outcomes.',
                '- Run a 2-week pilot with a success metric dashboard.'
            ].join('\n');
        }

        if (lower.includes('voice') || lower.includes('speech') || lower.includes('pashto') || lower.includes('sindhi')) {
            return [
                `Multilingual voice flow is enabled for ${profile.label} mode.`,
                '',
                '- Use the microphone button to start speech-to-text.',
                '- Select language from Settings (`Pashto - ps-AF`, `Sindhi - sd-PK`, and others).',
                '- Voice output can be toggled on with "Voice Response".',
                '',
                'If your browser does not support a locale directly, fallback recognition quality may vary by engine.'
            ].join('\n');
        }

        if (lower.includes('plan') || lower.includes('project')) {
            return [
                `Project delivery plan for ${profile.label}:`,
                '',
                '1. **Discovery**: clarify use cases and success metrics.',
                '2. **Pilot**: deploy chat + file + voice with one team.',
                '3. **Optimization**: refine prompts and workflow automation.',
                '4. **Scale**: onboard other departments with role-based playbooks.',
                fileContext
            ].join('\n');
        }

        return [
            `I can help you present this as a sellable ${profile.label} solution.`,
            '',
            '- Build market proposal and packaging',
            '- Analyze uploaded files for insights',
            '- Run multilingual speech recognition workflow',
            '- Create implementation timeline and pricing approach',
            '',
            'Tell me your target company type, and I will tailor the pitch.'
        ].join('\n');
    }

    function truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text || '';
        return `${text.slice(0, maxLength)}...`;
    }

    function clearChat() {
        if (!confirm('Are you sure you want to clear all chat messages?')) return;
        chatMessages.innerHTML = '';
        chatHistory = [];
        attachedFiles = [];
        localStorage.removeItem('chatHistory');
        welcomeMessage.style.display = 'block';
        showNotification('Chat and attached context cleared', 'success');
    }

    function loadChatHistory() {
        if (!chatHistory.length) return;
        welcomeMessage.style.display = 'none';
        chatHistory.forEach((msg) => addMessage(msg.text, msg.sender));
    }

    function saveChatHistory() {
        const messages = [];
        document.querySelectorAll('.message').forEach((msg) => {
            const sender = msg.classList.contains('user') ? 'user' : 'ai';
            const text = msg.querySelector('.message-text').textContent;
            messages.push({ sender, text });
        });
        chatHistory = messages.slice(-70);
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }

    function updateAnalytics() {
        const todayChats = document.getElementById('todayChats');
        const tasksCreated = document.getElementById('tasksCreated');

        todayChats.textContent = Number(todayChats.textContent) + 1;
        if (Math.random() > 0.65) {
            tasksCreated.textContent = Number(tasksCreated.textContent) + 1;
        }
    }

    function handleFileUpload(event) {
        const files = Array.from(event.target.files || []);
        if (!files.length) return;

        const allowedExtensions = ['txt', 'md', 'csv', 'json', 'log', 'py', 'js', 'ts', 'html', 'css'];
        const maxFileSizeBytes = 1024 * 1024 * 2;

        files.slice(0, 3).forEach((file) => {
            const ext = (file.name.split('.').pop() || '').toLowerCase();
            if (!allowedExtensions.includes(ext)) {
                showNotification(`Unsupported file type: ${file.name}`, 'warning');
                return;
            }
            if (file.size > maxFileSizeBytes) {
                showNotification(`File too large (>2MB): ${file.name}`, 'warning');
                return;
            }

            const reader = new FileReader();
            reader.onload = () => {
                const content = String(reader.result || '');
                attachedFiles.push({ name: file.name, content, size: file.size });
                attachedFiles = attachedFiles.slice(-5);
                addMessage(`Attached file: **${file.name}** (${Math.round(file.size / 1024)} KB)`, 'user');
                showNotification(`Loaded file: ${file.name}`, 'success');
                saveChatHistory();
            };
            reader.onerror = () => showNotification(`Could not read file: ${file.name}`, 'warning');
            reader.readAsText(file);
        });

        fileInput.value = '';
    }

    function initSpeechRecognition() {
        if (!SpeechRecognition) return;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = selectedSpeechLanguage;

        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i += 1) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) finalTranscript += transcript;
                else interimTranscript += transcript;
            }

            messageInput.value = finalTranscript || interimTranscript;
            messageInput.focus();
            messageInput.dispatchEvent(new Event('input'));
        };

        recognition.onend = () => {
            isRecording = false;
            voiceBtn.classList.remove('recording');
            showNotification('Voice input stopped', 'info');
        };

        recognition.onerror = (event) => {
            isRecording = false;
            voiceBtn.classList.remove('recording');
            showNotification(`Speech error: ${event.error}`, 'warning');
        };
    }

    function toggleVoiceInput() {
        if (!recognition) {
            showNotification('Speech recognition is not supported in this browser', 'warning');
            return;
        }
        if (isRecording) {
            recognition.stop();
            return;
        }
        recognition.lang = selectedSpeechLanguage;
        recognition.start();
        isRecording = true;
        voiceBtn.classList.add('recording');
        showNotification(`Listening in ${selectedSpeechLanguage}`, 'info');
    }

    function updateCompanyMode() {
        selectedCompanyMode = companyMode.value;
        localStorage.setItem('companyMode', selectedCompanyMode);
        applyCompanyBanner(selectedCompanyMode);
        showNotification(`Company mode: ${(companyProfiles[selectedCompanyMode] || {}).label || 'SMB'}`, 'success');
    }

    function applyCompanyBanner(mode) {
        const profile = companyProfiles[mode] || companyProfiles.smb;
        marketBannerText.textContent = profile.banner;
    }

    function updateSpeechLanguage() {
        selectedSpeechLanguage = speechLanguage.value;
        localStorage.setItem('speechLanguage', selectedSpeechLanguage);
        if (recognition) recognition.lang = selectedSpeechLanguage;
        showNotification(`Speech language set to ${selectedSpeechLanguage}`, 'info');
    }

    function speakIfEnabled(text) {
        if (!voiceToggle.checked) return;
        if (!window.speechSynthesis) {
            showNotification('Voice output not supported in this browser', 'warning');
            return;
        }
        const utterance = new SpeechSynthesisUtterance(text.replace(/\*+/g, '').replace(/`/g, ''));
        utterance.lang = selectedSpeechLanguage;
        utterance.rate = 1;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }

    function exportChat(event) {
        event.preventDefault();
        const lines = [];
        document.querySelectorAll('.message').forEach((msg) => {
            const sender = msg.classList.contains('user') ? 'USER' : 'ASSISTANT';
            const text = msg.querySelector('.message-text').textContent.trim();
            lines.push(`[${sender}] ${text}`);
        });
        if (!lines.length) {
            showNotification('No messages to export', 'warning');
            return;
        }
        const content = `# Chat Export\n\n${lines.join('\n\n')}\n`;
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `chat-export-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.md`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        showNotification('Chat exported', 'success');
    }

    function showHistorySnapshot(event) {
        event.preventDefault();
        if (!chatHistory.length) {
            showNotification('No saved history yet', 'info');
            return;
        }
        const total = chatHistory.length;
        const users = chatHistory.filter((m) => m.sender === 'user').length;
        const ai = total - users;
        addMessage(`History snapshot:\n- Total messages: ${total}\n- User: ${users}\n- Assistant: ${ai}`, 'ai');
    }

    function showModal(modal) {
        modal.style.display = 'flex';
    }

    function hideModal(modal) {
        modal.style.display = 'none';
    }

    function showNotification(message, type) {
        const iconMap = {
            success: 'fa-check-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas ${iconMap[type] || iconMap.info}"></i>
            <span>${escapeHtml(message)}</span>
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

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
            max-width: min(92vw, 460px);
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

    setTimeout(() => {
        if (!chatHistory.length) {
            showNotification('Welcome. Use company mode + voice + file upload to run your market demo.', 'info');
        }
    }, 900);
});
