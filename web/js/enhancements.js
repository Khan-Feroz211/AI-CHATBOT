// ============================================
// MODERN UI ENHANCEMENTS FOR PAKISTAN EDITION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initFloatingActionButton();
    initBusinessIndicator();
    initEnhancedAnimations();
    initSkeletonLoaders();
    initEmptyStates();
    initPaymentBadges();
    initUrduSupport();
});

// Floating Action Button (FAB) for quick actions
function initFloatingActionButton() {
    const fabHTML = `
        <div class="fab-container">
            <div class="fab-menu" id="fabMenu">
                <button class="fab-action" data-tooltip="Add Task" onclick="quickAddTask()">
                    <i class="fas fa-tasks"></i>
                </button>
                <button class="fab-action" data-tooltip="Voice Input" onclick="quickVoiceInput()">
                    <i class="fas fa-microphone"></i>
                </button>
                <button class="fab-action" data-tooltip="Payment Link" onclick="quickPayment()">
                    <i class="fas fa-money-bill-wave"></i>
                </button>
                <button class="fab-action" data-tooltip="Export Data" onclick="quickExport()">
                    <i class="fas fa-download"></i>
                </button>
            </div>
            <button class="fab-main" id="fabMain">
                <i class="fas fa-plus"></i>
            </button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', fabHTML);
    
    const fabMain = document.getElementById('fabMain');
    const fabMenu = document.getElementById('fabMenu');
    
    fabMain.addEventListener('click', () => {
        fabMenu.classList.toggle('active');
        const icon = fabMain.querySelector('i');
        icon.className = fabMenu.classList.contains('active') ? 'fas fa-times' : 'fas fa-plus';
    });
    
    // Close FAB menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.fab-container')) {
            fabMenu.classList.remove('active');
            fabMain.querySelector('i').className = 'fas fa-plus';
        }
    });
}

// Quick action functions
function quickAddTask() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = 'Add a task: ';
        messageInput.focus();
        document.getElementById('fabMenu').classList.remove('active');
    }
}

function quickVoiceInput() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.click();
        document.getElementById('fabMenu').classList.remove('active');
    }
}

function quickPayment() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = 'Create a payment link for order ORD-' + Date.now() + ' amount PKR 1000';
        messageInput.focus();
        document.getElementById('fabMenu').classList.remove('active');
    }
}

function quickExport() {
    const exportBtn = document.getElementById('exportChat');
    if (exportBtn) {
        exportBtn.click();
        document.getElementById('fabMenu').classList.remove('active');
    }
}

// Business type indicator
function initBusinessIndicator() {
    const businessType = localStorage.getItem('businessType') || 'general';
    const companyMode = localStorage.getItem('companyMode') || 'smb';
    
    const businessLabels = {
        general: '🏢 General Business',
        retail: '🏪 Kiryana Shop',
        restaurant: '🍽️ Restaurant',
        clinic: '⚕️ Clinic',
        service: '🔧 Service Business'
    };
    
    const indicatorHTML = `
        <div class="business-indicator pk-accent">
            <span>${businessLabels[businessType] || businessLabels.general}</span>
            <span style="opacity: 0.6;">•</span>
            <span style="text-transform: uppercase; font-size: 11px;">${companyMode}</span>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', indicatorHTML);
}

// Enhanced animations for interactions
function initEnhancedAnimations() {
    // Add ripple effect to buttons
    document.querySelectorAll('button, .action-btn, .suggestion-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: ripple 0.6s ease-out;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add CSS for ripple animation
    if (!document.getElementById('ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                from {
                    transform: scale(0);
                    opacity: 1;
                }
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Skeleton loaders for better perceived performance
function initSkeletonLoaders() {
    const chatMessages = document.getElementById('chatMessages');
    
    if (chatMessages && chatMessages.children.length === 0) {
        const skeletonHTML = `
            <div class="skeleton" style="height: 60px; margin-bottom: 16px; width: 70%;"></div>
            <div class="skeleton" style="height: 60px; margin-bottom: 16px; width: 85%; margin-left: auto;"></div>
            <div class="skeleton" style="height: 60px; margin-bottom: 16px; width: 60%;"></div>
        `;
        chatMessages.innerHTML = skeletonHTML;
        
        // Remove skeletons after content loads
        setTimeout(() => {
            document.querySelectorAll('.skeleton').forEach(el => el.remove());
        }, 1000);
    }
}

// Empty state handlers
function initEmptyStates() {
    // Check if chat is empty and show empty state
    const chatMessages = document.getElementById('chatMessages');
    
    const observer = new MutationObserver(() => {
        if (chatMessages && chatMessages.children.length === 0) {
            showEmptyState(chatMessages, 'chat');
        }
    });
    
    if (chatMessages) {
        observer.observe(chatMessages, { childList: true });
    }
}

function showEmptyState(container, type) {
    const emptyStates = {
        chat: {
            icon: '💬',
            title: 'No messages yet',
            description: 'Start a conversation with your AI assistant for Pakistan business operations'
        },
        tasks: {
            icon: '📋',
            title: 'No tasks found',
            description: 'Add your first task to start managing your work'
        },
        notes: {
            icon: '📝',
            title: 'No notes yet',
            description: 'Create notes to organize your business information'
        }
    };
    
    const state = emptyStates[type] || emptyStates.chat;
    
    const emptyHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">${state.icon}</div>
            <div class="empty-state-title">${state.title}</div>
            <div class="empty-state-description">${state.description}</div>
        </div>
    `;
    
    container.innerHTML = emptyHTML;
}

// Payment method badges
function initPaymentBadges() {
    const paymentMethod = document.getElementById('paymentMethod');
    
    if (paymentMethod) {
        paymentMethod.addEventListener('change', (e) => {
            const method = e.target.value;
            const badge = createPaymentBadge(method);
            
            // Show badge notification
            showNotification(`Payment method: ${badge}`, 'info');
        });
    }
}

function createPaymentBadge(method) {
    const badges = {
        jazzcash: '<span class="payment-badge jazzcash">💳 JazzCash</span>',
        easypaisa: '<span class="payment-badge easypaisa">💰 EasyPaisa</span>',
        bank_transfer: '<span class="payment-badge">🏦 Bank Transfer</span>',
        cod: '<span class="payment-badge">💵 Cash on Delivery</span>'
    };
    
    return badges[method] || badges.jazzcash;
}

// Urdu text support
function initUrduSupport() {
    const speechLanguage = document.getElementById('speechLanguage');
    
    if (speechLanguage) {
        speechLanguage.addEventListener('change', (e) => {
            const lang = e.target.value;
            
            if (lang === 'ur-PK') {
                document.body.classList.add('urdu-enabled');
                loadUrduFont();
            } else {
                document.body.classList.remove('urdu-enabled');
            }
        });
    }
}

function loadUrduFont() {
    if (!document.getElementById('urdu-font')) {
        const link = document.createElement('link');
        link.id = 'urdu-font';
        link.rel = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap';
        document.head.appendChild(link);
    }
}

// Enhanced notification system with Pakistan theme
function showNotificationEnhanced(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} pk-success`;
    
    const icons = {
        success: '✅',
        info: 'ℹ️',
        warning: '⚠️',
        error: '❌'
    };
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 20px;">${icons[type] || icons.info}</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Voice recording visual feedback
function showVoiceRecording() {
    const voiceIndicator = document.createElement('div');
    voiceIndicator.className = 'voice-recording';
    voiceIndicator.innerHTML = `
        <i class="fas fa-microphone"></i>
        <span>Recording...</span>
        <div class="voice-wave">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    const inputArea = document.querySelector('.input-area');
    if (inputArea) {
        inputArea.insertBefore(voiceIndicator, inputArea.firstChild);
    }
    
    return voiceIndicator;
}

function hideVoiceRecording(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => indicator.remove(), 300);
    }
}

// Smooth scroll to bottom for chat
function smoothScrollToBottom(element) {
    if (element) {
        element.scrollTo({
            top: element.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Copy to clipboard with feedback
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text).then(() => {
        showNotificationEnhanced(successMessage, 'success', 2000);
    }).catch(() => {
        showNotificationEnhanced('Failed to copy', 'error', 2000);
    });
}

// Format PKR currency
function formatPKR(amount) {
    return new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

// Add Pakistan-themed confetti for success actions
function celebratePakistanStyle() {
    const colors = ['#01411C', '#FFFFFF', '#FFD700']; // Pakistan flag colors + gold
    
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            left: ${Math.random() * 100}vw;
            top: -10px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            animation: confettiFall ${2 + Math.random() * 2}s linear forwards;
        `;
        
        document.body.appendChild(confetti);
        
        setTimeout(() => confetti.remove(), 4000);
    }
    
    // Add confetti animation if not exists
    if (!document.getElementById('confetti-style')) {
        const style = document.createElement('style');
        style.id = 'confetti-style';
        style.textContent = `
            @keyframes confettiFall {
                to {
                    transform: translateY(100vh) rotate(360deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Export enhanced functions for global use
window.quickAddTask = quickAddTask;
window.quickVoiceInput = quickVoiceInput;
window.quickPayment = quickPayment;
window.quickExport = quickExport;
window.showNotificationEnhanced = showNotificationEnhanced;
window.showVoiceRecording = showVoiceRecording;
window.hideVoiceRecording = hideVoiceRecording;
window.smoothScrollToBottom = smoothScrollToBottom;
window.copyToClipboard = copyToClipboard;
window.formatPKR = formatPKR;
window.celebratePakistanStyle = celebratePakistanStyle;
