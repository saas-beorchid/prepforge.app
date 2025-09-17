/**
 * Adaptive Practice JavaScript for PrepForge
 * Handles button/CTA interactions with Mixpanel tracking and adaptive question generation
 */

class AdaptivePracticeManager {
    constructor() {
        this.currentUser = null;
        this.currentQuestion = null;
        this.examType = null;
        this.topic = 'algebra'; // Default for GRE testing
        this.userScore = null;
        this.questionDifficulty = null;
        this.mixpanelReady = false;
        
        // Defer initialization until DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            // DOM is already ready
            this.init();
        }
    }
    
    init() {
        this.setupEventListeners();
        this.loadUserContext();
        this.initializeMixpanel();
    }
    
    initializeMixpanel() {
        // Check if Mixpanel is available (should be loaded from HTML)
        if (window.mixpanel && window.mixpanel.track) {
            console.log('✅ Mixpanel initialized for adaptive practice');
            this.mixpanelReady = true;
            return;
        }
        
        // Enhanced fallback: Wait for Mixpanel to load with exponential backoff
        let retries = 0;
        const maxRetries = 100; // 10+ seconds with exponential backoff
        this.mixpanelReady = false;
        
        const checkMixpanel = () => {
            if (window.mixpanel && window.mixpanel.track) {
                console.log('✅ Mixpanel loaded successfully for adaptive practice');
                this.mixpanelReady = true;
                return;
            }
            
            retries++;
            if (retries < maxRetries) {
                // Exponential backoff: start at 50ms, increase to max 500ms
                const delay = Math.min(50 * Math.pow(1.1, retries), 500);
                setTimeout(checkMixpanel, delay);
            } else {
                console.warn('⚠️ Mixpanel failed to load after extended timeout - continuing without analytics');
                this.mixpanelReady = false;
            }
        };
        
        checkMixpanel();
    }
    
    loadUserContext() {
        // Get user context from page data
        const userElement = document.querySelector('[data-user-id]');
        if (userElement) {
            this.currentUser = {
                id: parseInt(userElement.dataset.userId),
                email: userElement.dataset.userEmail
            };
        }
        
        // Get exam type from page
        const examElement = document.querySelector('[data-exam-type]');
        if (examElement) {
            this.examType = examElement.dataset.examType;
        }
        
        console.log('📊 User context loaded:', this.currentUser, 'Exam:', this.examType);
    }
    
    setupEventListeners() {
        // Practice form submission (Start Practice button)
        const practiceForm = document.querySelector('.exam-form');
        if (practiceForm) {
            practiceForm.addEventListener('submit', (e) => this.handleStartPractice(e));
        }
        
        // Generate Question buttons
        const generateBtns = document.querySelectorAll('[data-action="generate-question"]');
        generateBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleGenerateQuestion(e));
        });
        
        // Answer submission
        const answerForm = document.querySelector('.options-form');
        if (answerForm) {
            answerForm.addEventListener('submit', (e) => this.handleSubmitAnswer(e));
        }
        
        // Navigation buttons
        const navBtns = document.querySelectorAll('.nav-btn');
        navBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleNavigation(e));
        });
        
        // Quick action buttons on dashboard
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e));
        });
        
        // Exit practice button
        const exitBtn = document.querySelector('.exit-btn');
        if (exitBtn) {
            exitBtn.addEventListener('click', (e) => this.handleExitPractice(e));
        }
        
        // Enhanced Practice CTA buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.cta-button, .btn-primary, .start-practice-btn')) {
                this.handleCTAClick(e);
            }
        });
    }
    
    handleStartPractice(e) {
        const formData = new FormData(e.target);
        const examType = formData.get('exam_type');
        
        if (!examType) {
            e.preventDefault();
            this.showError('Please select an exam type');
            return;
        }
        
        this.trackEvent('Button Clicked', {
            action: 'start-practice',
            exam_type: examType,
            context: 'dashboard'
        });
        
        console.log('🚀 Starting practice for:', examType);
    }
    
    async handleGenerateQuestion(e) {
        e.preventDefault();
        
        const button = e.target.closest('button');
        const examType = this.examType || 'GRE';
        const topic = this.topic || 'algebra';
        
        this.trackEvent('Button Clicked', {
            action: 'generate-question',
            exam_type: examType,
            topic: topic,
            context: 'practice'
        });
        
        this.showLoading(button, 'Generating question...');
        
        try {
            // Get user performance first to determine difficulty
            const performance = await this.getUserPerformance(examType, topic);
            
            // Generate adaptive question
            const response = await this.generateAdaptiveQuestion(examType, topic);
            
            if (response.success) {
                this.displayQuestion(response.questions[0]);
                this.userScore = performance.score;
                this.questionDifficulty = response.questions[0].difficulty;
                
                this.trackEvent('Question Generated', {
                    exam_type: examType,
                    topic: topic,
                    difficulty: this.questionDifficulty,
                    user_score: this.userScore,
                    adaptive: true
                });
                
                console.log('✅ Generated question:', response.questions[0]);
            } else {
                throw new Error(response.error || 'Failed to generate question');
            }
            
        } catch (error) {
            console.error('❌ Error generating question:', error);
            this.showError('Failed to generate question: ' + error.message);
        } finally {
            this.hideLoading(button);
        }
    }
    
    async handleSubmitAnswer(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const selectedAnswer = formData.get('answer');
        
        if (!selectedAnswer) {
            this.showError('Please select an answer');
            return;
        }
        
        this.trackEvent('Button Clicked', {
            action: 'submit-answer',
            exam_type: this.examType,
            topic: this.topic,
            selected_answer: selectedAnswer,
            context: 'practice'
        });
        
        try {
            const response = await fetch(e.target.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayFeedback(result);
                
                // Update user performance if we have the data
                if (result.user_score !== undefined) {
                    await this.updateUserPerformance(this.examType, this.topic, result.user_score);
                }
                
                this.trackEvent('Answer Submitted', {
                    exam_type: this.examType,
                    topic: this.topic,
                    correct: result.correct,
                    selected_answer: selectedAnswer,
                    correct_answer: result.correct_answer,
                    difficulty: this.questionDifficulty,
                    context: 'practice'
                });
                
            } else {
                // Handle traditional form submission
                e.target.submit();
            }
            
        } catch (error) {
            console.error('❌ Error submitting answer:', error);
            // Fallback to traditional form submission
            e.target.submit();
        }
    }
    
    handleNavigation(e) {
        const action = e.target.dataset.action || 
                     (e.target.classList.contains('prev-btn') ? 'previous' : 'next');
        
        this.trackEvent('Button Clicked', {
            action: `navigate-${action}`,
            exam_type: this.examType,
            context: 'practice-navigation'
        });
    }
    
    handleQuickAction(e) {
        e.stopPropagation();
        
        const action = e.target.dataset.action;
        const examType = e.target.closest('.exam-card')?.dataset.examType;
        
        this.trackEvent('CTA Triggered', {
            action: action,
            exam_type: examType,
            context: 'dashboard-quick-action'
        });
        
        // Handle specific quick actions
        switch (action) {
            case 'quick-practice':
                this.startQuickPractice(examType);
                break;
            case 'view-progress':
                this.viewProgress(examType);
                break;
            case 'generate-questions':
                this.generateQuestions(examType);
                break;
        }
    }
    
    handleExitPractice(e) {
        this.trackEvent('Button Clicked', {
            action: 'exit-practice',
            exam_type: this.examType,
            context: 'practice'
        });
    }
    
    handleCTAClick(e) {
        const button = e.target;
        const action = button.dataset.action || 'cta-click';
        const context = button.dataset.context || 'general';
        
        this.trackEvent('CTA Triggered', {
            action: action,
            button_text: button.textContent.trim(),
            context: context,
            page: window.location.pathname
        });
    }
    
    // API Methods
    async getUserPerformance(examType, topic) {
        try {
            const response = await fetch(`/api/user-performance/${examType}/${topic}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            console.log('📊 User performance:', data);
            return data;
            
        } catch (error) {
            console.error('❌ Error getting user performance:', error);
            return { score: 50, difficulty_level: 'medium', attempts: 0 };
        }
    }
    
    async generateAdaptiveQuestion(examType, topic) {
        const response = await fetch('/api/generate-adaptive-questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                exam_type: examType,
                topic: topic,
                count: 1
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        return response.json();
    }
    
    async updateUserPerformance(examType, topic, score) {
        try {
            const response = await fetch('/api/update-performance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    exam_type: examType,
                    topic: topic,
                    score: score
                })
            });
            
            const data = await response.json();
            console.log('📊 Performance updated:', data);
            return data;
            
        } catch (error) {
            console.error('❌ Error updating performance:', error);
        }
    }
    
    // UI Methods
    displayQuestion(question) {
        const questionCard = document.querySelector('.question-card');
        if (!questionCard) return;
        
        const questionText = questionCard.querySelector('.question-text');
        if (questionText) {
            questionText.innerHTML = `<span class="math">${question.question}</span>`;
        }
        
        // Update options
        const optionsForm = questionCard.querySelector('.options-form');
        if (optionsForm && question.options) {
            const optionsHTML = Object.entries(question.options).map(([key, value]) => `
                <div class="option">
                    <input type="radio" name="answer" value="${key}" id="option${key}" required>
                    <label for="option${key}" class="option-text">
                        <span class="option-content math">${value}</span>
                    </label>
                </div>
            `).join('');
            
            const submitButton = optionsForm.querySelector('button[type="submit"]') || 
                               optionsForm.querySelector('.submit-btn');
            
            const existingOptions = optionsForm.querySelectorAll('.option');
            existingOptions.forEach(option => option.remove());
            
            if (submitButton) {
                submitButton.insertAdjacentHTML('beforebegin', optionsHTML);
            } else {
                optionsForm.innerHTML = optionsHTML + `
                    <button type="submit" class="btn btn-primary submit-btn">
                        Submit Answer
                    </button>
                `;
            }
        }
        
        // Re-initialize MathJax if available
        if (typeof MathJax !== 'undefined') {
            MathJax.typesetPromise([questionCard]).catch(err => 
                console.warn('MathJax typeset failed:', err)
            );
        }
        
        this.currentQuestion = question;
        console.log('🎯 Question displayed with difficulty:', question.difficulty);
    }
    
    displayFeedback(result) {
        // Implementation depends on the existing feedback system
        // This would integrate with the current practice.html feedback display
        console.log('📝 Feedback:', result);
    }
    
    showLoading(button, message = 'Loading...') {
        const originalText = button.textContent;
        button.disabled = true;
        button.dataset.originalText = originalText;
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${message}`;
    }
    
    hideLoading(button) {
        button.disabled = false;
        const originalText = button.dataset.originalText || 'Generate Question';
        button.textContent = originalText;
        delete button.dataset.originalText;
    }
    
    showError(message) {
        // Create or update error display
        let errorDiv = document.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message alert alert-danger';
            const container = document.querySelector('.practice-container') || 
                            document.querySelector('.dashboard-container') || 
                            document.body;
            container.insertBefore(errorDiv, container.firstChild);
        }
        
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        errorDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
    
    // Mixpanel tracking
    trackEvent(eventName, properties = {}) {
        // Only attempt tracking if Mixpanel is ready or give it a brief chance
        if (window.mixpanel && window.mixpanel.track) {
            const eventData = {
                user_id: this.currentUser?.id || 'anonymous',
                subscription_plan: 'free', // Default for adaptive practice
                exam_type: this.examType || 'unknown',
                topic: this.topic || null,
                timestamp: new Date().toISOString(),
                page: window.location.pathname,
                source: 'adaptive_practice',
                ...properties
            };
            
            try {
                window.mixpanel.track(eventName, eventData);
                console.log('📊 Tracked:', eventName, eventData);
                return true;
            } catch (error) {
                console.error('❌ Mixpanel tracking error:', error);
                return false;
            }
        } 
        
        // Silently fail if not ready - don't spam warnings
        if (this.mixpanelReady === false) {
            return false;
        }
        
        // Quick retry for edge cases where Mixpanel loaded but wasn't detected
        setTimeout(() => {
            if (window.mixpanel && window.mixpanel.track) {
                try {
                    const eventData = {
                        user_id: this.currentUser?.id || 'anonymous',
                        subscription_plan: 'free',
                        exam_type: this.examType || 'unknown',
                        topic: this.topic || null,
                        timestamp: new Date().toISOString(),
                        page: window.location.pathname,
                        source: 'adaptive_practice',
                        ...properties
                    };
                    window.mixpanel.track(eventName, eventData);
                    console.log('📊 Tracked (delayed):', eventName);
                } catch (error) {
                    // Silent fail on delayed attempts
                }
            }
        }, 100);
        
        return false;
    }
    
    // Additional utility methods
    startQuickPractice(examType) {
        window.location.href = `/practice?exam_type=${examType}`;
    }
    
    viewProgress(examType) {
        window.location.href = `/profile?exam_type=${examType}`;
    }
    
    generateQuestions(examType) {
        this.handleGenerateQuestion({ 
            target: { closest: () => ({ dataset: { examType } }) },
            preventDefault: () => {}
        });
    }
}

// Navigation functions removed - simplified exam flow

// Navigation with spinner removed - simplified exam flow

function exitPractice() {
    // Track the exit event
    const manager = window.adaptivePracticeManager;
    if (manager) {
        manager.trackEvent('Button Clicked', {
            action: 'exit-practice',
            exam_type: manager.examType,
            context: 'practice'
        });
    }
    
    // Existing exit logic
    if (confirm('Are you sure you want to exit practice? Your progress will be saved.')) {
        window.location.href = '/exit-practice';
    }
}

function exitPracticeWithSpinner(button) {
    // Show mobile-friendly exit modal instead of alert
    showExitModal(button);
}

function showExitModal(button) {
    // Create mobile-friendly exit modal
    const modal = document.createElement('div');
    modal.className = 'exit-modal-overlay';
    modal.innerHTML = `
        <div class="exit-modal">
            <div class="exit-modal-header">
                <h3>Exit Practice Session?</h3>
            </div>
            <div class="exit-modal-body">
                <p>Your progress will be saved and you can resume anytime.</p>
            </div>
            <div class="exit-modal-actions">
                <button class="btn btn-secondary" onclick="hideExitModal()">
                    Stay in Practice
                </button>
                <button class="btn btn-primary" onclick="confirmExitPractice()">
                    <span class="btn-text">Exit Practice</span>
                    <span class="btn-spinner" style="display: none;">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Saving...</span>
                    </span>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate in
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function hideExitModal() {
    const modal = document.querySelector('.exit-modal-overlay');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 300);
    }
}

function confirmExitPractice() {
    const exitBtn = document.querySelector('.exit-modal .btn-primary');
    showLoadingSpinner(exitBtn);
    
    // Track the exit event
    const manager = window.adaptivePracticeManager;
    if (manager) {
        manager.trackEvent('Button Clicked', {
            action: 'exit-practice',
            exam_type: manager.examType,
            context: 'practice'
        });
    }
    
    // Navigate to exit route
    window.location.href = '/exit-practice';
}

function showLoadingSpinner(button) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    
    if (btnText && btnSpinner) {
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline-flex';
        button.disabled = true;
    }
}

function hideLoadingSpinner(button) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    
    if (btnText && btnSpinner) {
        btnText.style.display = 'inline-flex';
        btnSpinner.style.display = 'none';
        button.disabled = false;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.adaptivePracticeManager = new AdaptivePracticeManager();
    console.log('🚀 Adaptive Practice Manager initialized');
});