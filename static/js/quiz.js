/**
 * Interactive Quiz System with API Integration
 * Handles question generation, answer submission, and user interactions
 */

class QuizApp {
    constructor() {
        this.currentQuestion = null;
        this.selectedAnswer = null;
        this.score = 0;
        this.questionsAnswered = 0;
        this.isAnswered = false;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeMixpanel();
    }
    
    initializeElements() {
        // Buttons
        this.generateBtn = document.getElementById('generate-question-btn');
        this.submitBtn = document.getElementById('submit-answer-btn');
        this.newQuestionBtn = document.getElementById('new-question-btn');
        this.upgradeBtn = document.getElementById('upgrade-btn');
        
        // Form elements
        this.examTypeSelect = document.getElementById('exam-type');
        this.topicInput = document.getElementById('topic');
        
        // Display elements
        this.questionContainer = document.getElementById('question-container');
        this.questionText = document.getElementById('question-text');
        this.questionOptions = document.getElementById('question-options');
        this.answerFeedback = document.getElementById('answer-feedback');
        this.feedbackResult = document.getElementById('feedback-result');
        this.correctAnswer = document.getElementById('correct-answer');
        this.explanation = document.getElementById('explanation');
        this.difficultyBadge = document.getElementById('difficulty-badge');
        this.userScore = document.getElementById('user-score');
        this.questionsRemaining = document.getElementById('questions-remaining');
        
        // Loading elements
        this.loading = document.getElementById('loading');
        this.loadingSpinner = document.getElementById('loading-spinner');
        this.answerLoading = document.getElementById('answer-loading');
        this.paymentLoading = document.getElementById('payment-loading');
        this.loadingText = document.getElementById('loading-text');
        this.loadingTimer = document.getElementById('loading-timer');
        
        // Error elements
        this.errorMessage = document.getElementById('error-message');
        this.errorText = document.getElementById('error-text');
        
        // Timer for loading feedback
        this.loadingStartTime = null;
        this.loadingInterval = null;
        
        console.log('✅ Quiz elements initialized');
    }
    
    bindEvents() {
        this.generateBtn.addEventListener('click', () => this.generateQuestion());
        this.submitBtn.addEventListener('click', () => this.submitAnswer());
        this.newQuestionBtn.addEventListener('click', () => this.resetForNewQuestion());
        this.upgradeBtn.addEventListener('click', () => this.upgradeToPro());
        
        // Exit practice button
        const exitBtn = document.getElementById('exit-practice-btn');
        if (exitBtn) {
            exitBtn.addEventListener('click', () => this.exitPractice());
        }
        
        // Option selection
        this.questionOptions.addEventListener('click', (e) => {
            if (e.target.closest('.option') && !this.isAnswered) {
                this.selectOption(e.target.closest('.option'));
            }
        });
    }
    
    initializeMixpanel() {
        // Check if Mixpanel is available (should be loaded from HTML)
        if (window.mixpanel && window.mixpanel.track) {
            console.log('✅ Mixpanel already initialized from HTML');
            return;
        }
        
        // Fallback: Wait for Mixpanel to load
        let retries = 0;
        const maxRetries = 50; // 5 seconds
        const checkMixpanel = () => {
            if (window.mixpanel && window.mixpanel.track) {
                console.log('✅ Mixpanel loaded successfully');
                return;
            }
            
            retries++;
            if (retries < maxRetries) {
                setTimeout(checkMixpanel, 100);
            } else {
                console.warn('⚠️ Mixpanel failed to load after 5 seconds');
            }
        };
        
        checkMixpanel();
    }
    
    trackEvent(eventName, properties = {}) {
        if (window.mixpanel && window.mixpanel.track) {
            const baseProperties = {
                user_id: window.userId || 'anonymous',
                subscription_plan: window.userPlan || 'free',
                exam_type: this.examTypeSelect?.value || 'unknown',
                topic: this.topicInput?.value || null,
                timestamp: new Date().toISOString(),
                source: 'quiz_interface'
            };
            
            try {
                window.mixpanel.track(eventName, { ...baseProperties, ...properties });
                console.log(`📊 Tracked: ${eventName}`, { ...baseProperties, ...properties });
            } catch (error) {
                console.error('❌ Mixpanel tracking error:', error);
            }
        } else {
            console.warn('⚠️ Mixpanel not available for tracking:', eventName);
        }
    }
    
    async generateQuestion() {
        try {
            this.showLoading('question', 'Generating question...');
            this.hideError();
            
            const examType = this.examTypeSelect.value;
            const topic = this.topicInput.value.trim() || null;
            
            this.trackEvent('Button Clicked', {
                action: 'generate_question',
                exam_type: examType,
                topic: topic
            });
            
            const response = await fetch('/api/generate-questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    exam_type: examType,
                    topic: topic,
                    count: 1
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 429) {
                    // Rate limit exceeded - show upgrade option
                    this.handleRateLimit(data.message);
                    return;
                }
                throw new Error(data.error || `Server error: ${response.status}`);
            }
            
            if (data.questions && data.questions.length > 0) {
                this.displayQuestion(data.questions[0]);
                this.trackEvent('Question Generated', {
                    question_id: data.questions[0].id || 'generated',
                    difficulty: data.questions[0].difficulty || 'unknown'
                });
            } else {
                throw new Error('No questions received from server');
            }
            
        } catch (error) {
            console.error('Error generating question:', error);
            this.showError(`Failed to generate question: ${error.message}`);
            this.trackEvent('Error Occurred', {
                action: 'generate_question',
                error_message: error.message
            });
        } finally {
            this.hideLoading();
        }
    }
    
    displayQuestion(question) {
        this.currentQuestion = question;
        this.selectedAnswer = null;
        this.isAnswered = false;
        
        // Update question content
        this.questionText.innerHTML = question.question_text || question.question;
        
        // Update difficulty badge
        const difficulty = question.difficulty || 'medium';
        this.difficultyBadge.textContent = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
        this.difficultyBadge.className = `difficulty-badge ${difficulty}`;
        
        // Display options
        this.questionOptions.innerHTML = '';
        const options = question.choices || question.options || [];
        
        options.forEach((option, index) => {
            const optionElement = document.createElement('div');
            optionElement.className = 'option';
            optionElement.dataset.value = String.fromCharCode(65 + index); // A, B, C, D
            
            // Clean choice text - remove existing letter prefixes (A., B., etc.) to prevent "A A. Choice"
            let cleanOption = option;
            if (typeof option === 'string') {
                cleanOption = option.replace(/^[A-D][.)]\s*/, '').trim();
            }
            
            optionElement.innerHTML = `
                <span class="option-content">${cleanOption}</span>
            `;
            
            this.questionOptions.appendChild(optionElement);
        });
        
        // Show question container and reset UI
        this.questionContainer.style.display = 'block';
        this.answerFeedback.style.display = 'none';
        this.submitBtn.disabled = true;
        this.newQuestionBtn.style.display = 'none';
        
        // Render math if present
        if (window.MathJax) {
            MathJax.typesetPromise([this.questionContainer]).catch(err => {
                console.warn('MathJax rendering error:', err);
            });
        }
    }
    
    selectOption(optionElement) {
        // Remove previous selection
        document.querySelectorAll('.option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Select current option
        optionElement.classList.add('selected');
        this.selectedAnswer = optionElement.dataset.value;
        this.submitBtn.disabled = false;
    }
    
    async submitAnswer() {
        if (!this.selectedAnswer || this.isAnswered) return;
        
        try {
            this.showLoading('answer', 'Checking answer...');
            this.submitBtn.disabled = true;
            
            this.trackEvent('Button Clicked', {
                action: 'submit_answer',
                selected_answer: this.selectedAnswer,
                question_id: this.currentQuestion.id || 'generated'
            });
            
            const response = await fetch('/api/submit-answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id || 'temp',
                    answer: this.selectedAnswer,
                    exam_type: this.examTypeSelect.value,
                    question_data: this.currentQuestion
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }
            
            this.displayEnhancedFeedback(data);
            this.isAnswered = true;
            
        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showError(`Failed to submit answer: ${error.message}`);
            this.trackEvent('Error Occurred', {
                action: 'submit_answer',
                error_message: error.message
            });
        } finally {
            this.hideLoading();
        }
    }
    
    displayAnswerFeedback(result) {
        const isCorrect = result.is_correct || result.correct;
        const correctAnswer = result.correct_answer || this.currentQuestion.correct_answer;
        const explanation = result.explanation || this.currentQuestion.explanation;
        
        // Update score
        if (isCorrect) {
            this.score++;
        }
        this.questionsAnswered++;
        this.userScore.textContent = `Score: ${this.score}/${this.questionsAnswered}`;
        
        // Update remaining questions for free users
        if (window.userPlan === 'free' && result.questions_remaining !== undefined) {
            this.questionsRemaining.textContent = `${result.questions_remaining} left`;
        }
        
        // Highlight correct/incorrect options
        document.querySelectorAll('.option').forEach(option => {
            const optionValue = option.dataset.value;
            if (optionValue === correctAnswer) {
                option.classList.add('correct');
            } else if (optionValue === this.selectedAnswer && !isCorrect) {
                option.classList.add('incorrect');
            }
        });
        
        // Show feedback
        this.feedbackResult.innerHTML = isCorrect 
            ? '<i class="fas fa-check-circle"></i> Correct!' 
            : '<i class="fas fa-times-circle"></i> Incorrect';
        this.feedbackResult.className = `feedback-result ${isCorrect ? 'correct' : 'incorrect'}`;
        
        this.correctAnswer.innerHTML = `<strong>Correct Answer:</strong> ${correctAnswer}`;
        this.explanation.innerHTML = explanation || 'No explanation available.';
        
        this.answerFeedback.style.display = 'block';
        this.newQuestionBtn.style.display = 'inline-flex';
        
        // Render math in feedback
        if (window.MathJax) {
            MathJax.typesetPromise([this.answerFeedback]).catch(err => {
                console.warn('MathJax rendering error:', err);
            });
        }
        
        // Track answer result
        this.trackEvent('Answer Submitted', {
            is_correct: isCorrect,
            correct_answer: correctAnswer,
            user_answer: this.selectedAnswer,
            score: this.score,
            questions_answered: this.questionsAnswered
        });
    }
    
    resetForNewQuestion() {
        this.questionContainer.style.display = 'none';
        this.answerFeedback.style.display = 'none';
        this.selectedAnswer = null;
        this.isAnswered = false;
        this.hideError();
        
        // Track next question event
        this.trackEvent('Button Clicked', {
            action: 'next_question',
            current_score: this.score,
            questions_answered: this.questionsAnswered
        });
        
        // Automatically generate next question
        this.generateQuestion();
    }
    
    handleRateLimit(message) {
        this.showError(message || 'Daily question limit reached. Upgrade to Pro for unlimited questions!');
        this.upgradeBtn.style.display = 'inline-flex';
        
        this.trackEvent('Rate Limit Hit', {
            exam_type: this.examTypeSelect.value,
            questions_answered: this.questionsAnswered,
            score: this.score
        });
    }
    
    addExitButton() {
        // Add exit button to quiz interface
        const exitBtn = document.createElement('button');
        exitBtn.id = 'exit-practice-btn';
        exitBtn.className = 'btn btn-secondary';
        exitBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Exit Practice';
        exitBtn.onclick = () => this.exitPractice();
        
        // Add to quiz actions
        const quizActions = document.querySelector('.quiz-actions');
        if (quizActions && !document.getElementById('exit-practice-btn')) {
            quizActions.appendChild(exitBtn);
        }
    }
    
    exitPractice() {
        // Track exit event
        this.trackEvent('Practice Exited', {
            exam_type: this.examTypeSelect.value,
            questions_answered: this.questionsAnswered,
            score: this.score,
            exit_method: 'button_click'
        });
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
        
        this.trackEvent('Rate Limit Reached', {
            message: message
        });
    }
    
    async upgradeToPro() {
        console.log('🚀 upgradeToPro started');
        
        try {
            console.log('📊 Tracking upgrade button click event');
            this.trackEvent('Upgrade Button Clicked', {
                action: 'upgrade_to_pro'
            });
            
            console.log('⏳ Showing payment loading state');
            this.showLoading('payment', 'Creating checkout session...');
            
            console.log('📡 Sending request to /create-checkout-session');
            const startTime = Date.now();
            
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const responseTime = Date.now() - startTime;
            console.log('📥 Fetch response received:', {
                status: response.status,
                ok: response.ok,
                contentType: response.headers.get('Content-Type'),
                responseTime: responseTime + 'ms'
            });
            
            const data = await response.json();
            console.log('📋 Response data:', data);
            
            if (!response.ok) {
                console.error('❌ Response not OK:', response.status);
                throw new Error(data.error || 'Failed to create checkout session');
            }
            
            if (data.success && data.client_secret) {
                console.log('✅ Checkout session created successfully');
                console.log('🔑 Client Secret received for embedded checkout');
                console.log('🆔 Session ID:', data.session_id);
                console.log('⏱️ Total processing time:', responseTime + 'ms');
                console.log('🚀 Starting embedded checkout...');
                
                // Load and initialize embedded checkout
                this.hideLoading();
                await this.initializeEmbeddedCheckout(data.client_secret);
                
            } else {
                console.error('❌ Invalid response format - missing client_secret');
                throw new Error('No client secret received for embedded checkout');
            }
            
        } catch (error) {
            console.error('❌ Error upgrading to pro:', error);
            this.hideLoading();
            this.showError(`Failed to start upgrade process: ${error.message}`);
            this.trackEvent('Error Occurred', {
                action: 'upgrade_to_pro',
                error_message: error.message
            });
        }
    }
    
    async initializeEmbeddedCheckout(clientSecret) {
        try {
            console.log('🏗️ Initializing embedded Stripe checkout...');
            
            // Load Stripe if not already loaded
            if (!window.Stripe) {
                console.log('📦 Loading Stripe.js...');
                await new Promise((resolve) => {
                    const script = document.createElement('script');
                    script.src = 'https://js.stripe.com/v3/';
                    script.onload = resolve;
                    document.head.appendChild(script);
                });
            }
            
            const stripe = Stripe('pk_test_your_publishable_key_here'); // Will be configured properly
            
            // Create checkout container
            const container = this.createCheckoutContainer();
            
            // Initialize embedded checkout
            const checkout = await stripe.initEmbeddedCheckout({
                clientSecret: clientSecret
            });
            
            checkout.mount('#embedded-checkout-container');
            container.style.display = 'block';
            
            console.log('✅ Embedded checkout mounted successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize embedded checkout:', error);
            this.showError('Failed to load checkout. Please try again.');
        }
    }
    
    createCheckoutContainer() {
        let overlay = document.getElementById('checkout-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'checkout-overlay';
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.8); z-index: 10000; display: none;
                overflow-y: auto; padding: 2rem; box-sizing: border-box;
            `;
            
            const container = document.createElement('div');
            container.id = 'embedded-checkout-container';
            container.style.cssText = `
                max-width: 600px; margin: 0 auto; background: white;
                border-radius: 12px; padding: 2rem; position: relative; min-height: 400px;
            `;
            
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '&times;';
            closeButton.style.cssText = `
                position: absolute; top: 1rem; right: 1rem; background: none;
                border: none; font-size: 2rem; cursor: pointer; color: #666; z-index: 1;
            `;
            closeButton.onclick = () => this.closeCheckout();
            
            container.appendChild(closeButton);
            overlay.appendChild(container);
            document.body.appendChild(overlay);
            
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.closeCheckout();
            });
        }
        
        return overlay;
    }
    
    closeCheckout() {
        const overlay = document.getElementById('checkout-overlay');
        if (overlay) overlay.style.display = 'none';
    }
    
    showLoading(type = 'question', text = 'Generating question...') {
        console.log(`⏳ Showing ${type} loading state: ${text}`);
        
        // Hide all loading states first
        this.hideAllLoading();
        
        let loadingElement;
        switch(type) {
            case 'answer':
                loadingElement = document.getElementById('answer-loading');
                break;
            case 'payment':
                loadingElement = document.getElementById('payment-loading');
                break;
            default:
                loadingElement = this.loading;
                const loadingText = document.getElementById('loading-text');
                if (loadingText) loadingText.textContent = text;
        }
        
        if (loadingElement) {
            loadingElement.style.display = 'block';
            
            // Start timer for question generation
            if (type === 'question') {
                this.startLoadingTimer();
            }
        }
        
        this.generateBtn.disabled = true;
        if (this.submitBtn) this.submitBtn.disabled = true;
    }
    
    hideLoading() {
        console.log('✅ Hiding loading state');
        this.hideAllLoading();
        this.generateBtn.disabled = false;
        if (this.submitBtn && this.selectedAnswer) {
            this.submitBtn.disabled = false;
        }
        this.stopLoadingTimer();
    }
    
    hideAllLoading() {
        const loadingElements = [
            this.loading,
            document.getElementById('answer-loading'),
            document.getElementById('payment-loading')
        ];
        
        loadingElements.forEach(element => {
            if (element) element.style.display = 'none';
        });
    }
    
    startLoadingTimer() {
        this.loadingStartTime = Date.now();
        this.loadingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.loadingStartTime) / 1000);
            const timerElement = document.getElementById('loading-timer-text');
            if (timerElement) {
                timerElement.textContent = `${elapsed}s`;
                
                // Warn if loading takes too long
                if (elapsed > 5) {
                    timerElement.style.color = 'var(--warning-orange)';
                    console.warn('⚠️ Loading taking longer than expected:', elapsed + 's');
                }
            }
        }, 1000);
    }
    
    stopLoadingTimer() {
        if (this.loadingTimer) {
            clearInterval(this.loadingTimer);
            this.loadingTimer = null;
        }
        
        const timerElement = document.getElementById('loading-timer-text');
        if (timerElement) {
            timerElement.textContent = '0s';
            timerElement.style.color = '';
        }
    }
    
    showError(message) {
        this.errorText.textContent = message;
        this.errorMessage.style.display = 'block';
    }
    
    hideError() {
        this.errorMessage.style.display = 'none';
    }
}

// Global functions for explanation toggling
function toggleExplanation(type) {
    console.log(`🔄 Toggling explanation: ${type}`);
    
    const explanationContent = document.getElementById(`explanation-${type}`);
    const header = explanationContent?.previousElementSibling;
    const toggleIcon = header?.querySelector('.toggle-icon');
    
    if (explanationContent) {
        const isCollapsed = explanationContent.classList.contains('collapsed');
        
        if (isCollapsed) {
            explanationContent.classList.remove('collapsed');
            explanationContent.classList.add('expanded');
            if (toggleIcon) toggleIcon.style.transform = 'rotate(180deg)';
            console.log(`📖 Expanded ${type} explanation`);
        } else {
            explanationContent.classList.remove('expanded');
            explanationContent.classList.add('collapsed');
            if (toggleIcon) toggleIcon.style.transform = 'rotate(0deg)';
            console.log(`📚 Collapsed ${type} explanation`);
        }
        
        // Re-render MathJax if needed
        if (window.MathJax && !isCollapsed) {
            MathJax.typesetPromise([explanationContent]).catch(err => {
                console.warn('MathJax rendering error:', err);
            });
        }
    }
}

// Initialize quiz app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Quiz App');
    window.quizApp = new QuizApp();
    
    // Add hamburger menu functionality
    initializeHamburgerMenu();
    
    console.log('✅ Quiz App initialized successfully');
});

// Enhanced hamburger menu initialization with mobile event binding
function initializeHamburgerMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (mobileMenuToggle && mainNav) {
        console.log('🍔 Initializing hamburger menu functionality');
        
        // Enhanced click/touch event binding for mobile
        ['click', 'touchstart'].forEach(eventType => {
            mobileMenuToggle.addEventListener(eventType, function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log(`🍔 Hamburger menu ${eventType} triggered`);
                
                // Toggle active class on both menu and toggle button
                const isActive = mainNav.classList.contains('active');
                
                mainNav.classList.toggle('active');
                this.classList.toggle('active');
                
                // Update aria-expanded attribute for accessibility
                this.setAttribute('aria-expanded', !isActive);
                
                console.log('📱 Mobile menu toggled:', !isActive ? 'open' : 'closed');
            }, { passive: false });
        });
        
        // Close mobile menu when clicking on nav links
        const navLinks = mainNav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                mainNav.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                console.log('📱 Mobile menu closed after link click');
            });
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuToggle.contains(e.target) && !mainNav.contains(e.target)) {
                mainNav.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        console.log('✅ Hamburger menu initialized with enhanced mobile support');
    } else {
        console.warn('⚠️ Hamburger menu elements not found');
    }
}

// Global function for toggling explanations
function toggleExplanation(type) {
    const content = document.getElementById(`explanation-${type}`);
    const header = content.previousElementSibling;
    const icon = header.querySelector('.toggle-icon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        content.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
        console.log(`📖 Expanded ${type} explanation`);
    } else {
        content.classList.add('collapsed');
        content.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
        console.log(`📕 Collapsed ${type} explanation`);
    }
}

// Initialize quiz app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quizApp = new QuizApp();
    console.log('✅ Quiz app initialized successfully');
});