// Enhanced Practice Interface with Adaptive Features

class EnhancedPracticeManager {
    constructor() {
        this.startTime = null;
        this.questionStartTime = null;
        this.confidenceLevel = null;
        this.hintCount = 0;
        this.sessionData = {
            questions_answered: 0,
            correct_answers: 0,
            total_time: 0,
            average_confidence: 0
        };
        this.adaptiveSettings = {
            target_accuracy: 0.75,
            difficulty_adjustment: true,
            time_pressure: false
        };
        this.init();
    }

    init() {
        this.initQuestionTimer();
        this.initConfidenceTracker();
        this.initHintSystem();
        this.initProgressTracking();
        this.initKeyboardShortcuts();
        this.initAdaptiveInterface();
    }

    initQuestionTimer() {
        this.questionStartTime = Date.now();
        
        // Create timer display
        const timerContainer = document.createElement('div');
        timerContainer.className = 'question-timer';
        timerContainer.innerHTML = `
            <div class="timer-display">
                <i class="fas fa-clock"></i>
                <span class="time-value">00:00</span>
            </div>
        `;
        
        const questionContainer = document.querySelector('.question-container');
        if (questionContainer) {
            questionContainer.insertBefore(timerContainer, questionContainer.firstChild);
        }
        
        // Start timer
        this.timerInterval = setInterval(() => {
            this.updateTimer();
        }, 1000);
    }

    updateTimer() {
        if (!this.questionStartTime) return;
        
        const elapsed = Math.floor((Date.now() - this.questionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        const timerDisplay = document.querySelector('.time-value');
        if (timerDisplay) {
            timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Add visual warnings for time pressure
            if (elapsed > 180) { // 3 minutes
                timerDisplay.parentElement.classList.add('timer-warning');
            }
            if (elapsed > 300) { // 5 minutes
                timerDisplay.parentElement.classList.add('timer-danger');
            }
        }
    }

    initConfidenceTracker() {
        // Add confidence selector to the interface
        const confidenceHTML = `
            <div class="confidence-tracker">
                <h6 class="confidence-label">How confident are you?</h6>
                <div class="confidence-scale">
                    <button type="button" class="confidence-btn" data-confidence="1">
                        <i class="fas fa-frown"></i>
                        <span>Not Sure</span>
                    </button>
                    <button type="button" class="confidence-btn" data-confidence="2">
                        <i class="fas fa-meh"></i>
                        <span>Somewhat</span>
                    </button>
                    <button type="button" class="confidence-btn" data-confidence="3">
                        <i class="fas fa-smile"></i>
                        <span>Confident</span>
                    </button>
                    <button type="button" class="confidence-btn" data-confidence="4">
                        <i class="fas fa-grin"></i>
                        <span>Very Sure</span>
                    </button>
                </div>
            </div>
        `;
        
        const choicesContainer = document.querySelector('.choices-container');
        if (choicesContainer) {
            choicesContainer.insertAdjacentHTML('afterend', confidenceHTML);
            
            // Add event listeners
            document.querySelectorAll('.confidence-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelectorAll('.confidence-btn').forEach(b => b.classList.remove('selected'));
                    e.target.closest('.confidence-btn').classList.add('selected');
                    this.confidenceLevel = parseInt(e.target.closest('.confidence-btn').dataset.confidence);
                });
            });
        }
    }

    initHintSystem() {
        // Add hint button
        const hintHTML = `
            <div class="hint-system">
                <button type="button" class="btn btn-outline-info hint-btn" id="request-hint">
                    <i class="fas fa-lightbulb"></i> Get Hint
                    <span class="hint-count">(${this.hintCount}/2)</span>
                </button>
                <div class="hint-display" id="hint-display" style="display: none;"></div>
            </div>
        `;
        
        const questionText = document.querySelector('.question-text');
        if (questionText) {
            questionText.insertAdjacentHTML('afterend', hintHTML);
            
            document.getElementById('request-hint').addEventListener('click', () => {
                this.requestHint();
            });
        }
    }

    async requestHint() {
        if (this.hintCount >= 2) {
            this.showNotification('Maximum hints reached for this question', 'warning');
            return;
        }
        
        try {
            const questionId = this.getCurrentQuestionId();
            const response = await fetch('/api/get-hint', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_id: questionId,
                    hint_number: this.hintCount + 1
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayHint(result.hint);
                this.hintCount++;
                this.updateHintButton();
            } else {
                this.showNotification('Hint not available for this question', 'info');
            }
        } catch (error) {
            console.error('Error requesting hint:', error);
            this.showNotification('Unable to load hint at this time', 'error');
        }
    }

    displayHint(hintText) {
        const hintDisplay = document.getElementById('hint-display');
        if (hintDisplay) {
            hintDisplay.innerHTML = `
                <div class="hint-content">
                    <i class="fas fa-lightbulb text-warning"></i>
                    <span>${hintText}</span>
                </div>
            `;
            hintDisplay.style.display = 'block';
            
            // Animate hint appearance
            hintDisplay.style.opacity = '0';
            hintDisplay.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                hintDisplay.style.transition = 'all 0.3s ease';
                hintDisplay.style.opacity = '1';
                hintDisplay.style.transform = 'translateY(0)';
            }, 100);
        }
    }

    updateHintButton() {
        const hintBtn = document.getElementById('request-hint');
        const hintCount = document.querySelector('.hint-count');
        
        if (hintCount) {
            hintCount.textContent = `(${this.hintCount}/2)`;
        }
        
        if (this.hintCount >= 2 && hintBtn) {
            hintBtn.disabled = true;
            hintBtn.innerHTML = '<i class="fas fa-ban"></i> No more hints';
        }
    }

    initProgressTracking() {
        // Track session progress
        this.startTime = Date.now();
        
        // Create progress indicator
        const progressHTML = `
            <div class="session-progress">
                <div class="progress-stats">
                    <span class="stat">
                        <i class="fas fa-chart-line"></i>
                        <span class="stat-value" id="session-accuracy">0%</span>
                        <span class="stat-label">Accuracy</span>
                    </span>
                    <span class="stat">
                        <i class="fas fa-clock"></i>
                        <span class="stat-value" id="average-time">0s</span>
                        <span class="stat-label">Avg Time</span>
                    </span>
                    <span class="stat">
                        <i class="fas fa-target"></i>
                        <span class="stat-value" id="questions-count">0</span>
                        <span class="stat-label">Questions</span>
                    </span>
                </div>
            </div>
        `;
        
        const practiceHeader = document.querySelector('.practice-header');
        if (practiceHeader) {
            practiceHeader.insertAdjacentHTML('beforeend', progressHTML);
        }
    }

    updateSessionProgress(isCorrect) {
        this.sessionData.questions_answered++;
        if (isCorrect) {
            this.sessionData.correct_answers++;
        }
        
        const responseTime = Math.floor((Date.now() - this.questionStartTime) / 1000);
        this.sessionData.total_time += responseTime;
        
        if (this.confidenceLevel) {
            this.sessionData.average_confidence = 
                (this.sessionData.average_confidence * (this.sessionData.questions_answered - 1) + this.confidenceLevel) 
                / this.sessionData.questions_answered;
        }
        
        // Update UI
        const accuracy = (this.sessionData.correct_answers / this.sessionData.questions_answered * 100).toFixed(1);
        const avgTime = Math.floor(this.sessionData.total_time / this.sessionData.questions_answered);
        
        document.getElementById('session-accuracy').textContent = accuracy + '%';
        document.getElementById('average-time').textContent = avgTime + 's';
        document.getElementById('questions-count').textContent = this.sessionData.questions_answered;
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only activate in practice mode
            if (!document.querySelector('.practice-container')) return;
            
            switch(e.key) {
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                    e.preventDefault();
                    this.selectChoice(parseInt(e.key) - 1);
                    break;
                case 'Enter':
                    e.preventDefault();
                    this.submitAnswer();
                    break;
                case 'h':
                case 'H':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.requestHint();
                    }
                    break;
                case 'n':
                case 'N':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.skipQuestion();
                    }
                    break;
            }
        });
        
        // Add keyboard shortcuts legend
        const shortcutsHTML = `
            <div class="keyboard-shortcuts" style="display: none;">
                <h6>Keyboard Shortcuts</h6>
                <ul>
                    <li><kbd>1-5</kbd> Select answer choice</li>
                    <li><kbd>Enter</kbd> Submit answer</li>
                    <li><kbd>Ctrl+H</kbd> Request hint</li>
                    <li><kbd>Ctrl+N</kbd> Skip question</li>
                </ul>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', shortcutsHTML);
        
        // Toggle shortcuts with ?
        document.addEventListener('keydown', (e) => {
            if (e.key === '?' && e.shiftKey) {
                const shortcuts = document.querySelector('.keyboard-shortcuts');
                shortcuts.style.display = shortcuts.style.display === 'none' ? 'block' : 'none';
            }
        });
    }

    selectChoice(index) {
        const choices = document.querySelectorAll('.choice-button, .choice-item');
        if (choices[index]) {
            choices.forEach(choice => choice.classList.remove('selected'));
            choices[index].classList.add('selected');
            choices[index].click();
        }
    }

    submitAnswer() {
        const submitBtn = document.querySelector('#submit-answer, .submit-btn');
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.click();
        }
    }

    skipQuestion() {
        const skipBtn = document.querySelector('.skip-btn');
        if (skipBtn) {
            skipBtn.click();
        }
    }

    initAdaptiveInterface() {
        // Add adaptive controls
        const adaptiveHTML = `
            <div class="adaptive-controls" style="display: none;">
                <h6>Learning Preferences</h6>
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="difficulty-adjustment" checked>
                        Adaptive difficulty
                    </label>
                </div>
                <div class="control-group">
                    <label>
                        Target accuracy: <span id="target-display">75%</span>
                    </label>
                    <input type="range" id="target-accuracy" min="60" max="90" value="75" step="5">
                </div>
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="time-pressure">
                        Enable time pressure mode
                    </label>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', adaptiveHTML);
        
        // Event listeners for adaptive controls
        document.getElementById('target-accuracy').addEventListener('input', (e) => {
            document.getElementById('target-display').textContent = e.target.value + '%';
            this.adaptiveSettings.target_accuracy = e.target.value / 100;
        });
        
        document.getElementById('difficulty-adjustment').addEventListener('change', (e) => {
            this.adaptiveSettings.difficulty_adjustment = e.target.checked;
        });
        
        document.getElementById('time-pressure').addEventListener('change', (e) => {
            this.adaptiveSettings.time_pressure = e.target.checked;
            this.toggleTimePressureMode(e.target.checked);
        });
    }

    toggleTimePressureMode(enabled) {
        if (enabled) {
            // Add visual time pressure indicators
            document.body.classList.add('time-pressure-mode');
        } else {
            document.body.classList.remove('time-pressure-mode');
        }
    }

    // Enhanced answer submission with all tracking data
    async submitAnswerWithTracking(selectedAnswer) {
        const responseTime = Math.floor((Date.now() - this.questionStartTime) / 1000);
        const questionId = this.getCurrentQuestionId();
        
        const submissionData = {
            question_id: questionId,
            selected_answer: selectedAnswer,
            response_time: responseTime,
            confidence_level: this.confidenceLevel || 3,
            hints_used: this.hintCount,
            session_data: this.sessionData,
            adaptive_settings: this.adaptiveSettings
        };
        
        try {
            const response = await fetch('/api/submit-answer-enhanced', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submissionData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateSessionProgress(result.is_correct);
                this.resetQuestionState();
                
                // Handle adaptive difficulty adjustment
                if (this.adaptiveSettings.difficulty_adjustment && result.next_difficulty) {
                    this.adjustDifficulty(result.next_difficulty);
                }
                
                return result;
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showNotification('Error submitting answer', 'error');
        }
    }

    resetQuestionState() {
        // Reset question-specific state
        this.questionStartTime = Date.now();
        this.confidenceLevel = null;
        this.hintCount = 0;
        
        // Reset UI elements
        document.querySelectorAll('.confidence-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        const hintDisplay = document.getElementById('hint-display');
        if (hintDisplay) {
            hintDisplay.style.display = 'none';
        }
        
        this.updateHintButton();
        
        // Clear timer warnings
        const timerDisplay = document.querySelector('.timer-display');
        if (timerDisplay) {
            timerDisplay.classList.remove('timer-warning', 'timer-danger');
        }
    }

    adjustDifficulty(newDifficulty) {
        // Visual feedback for difficulty adjustment
        const notification = `Difficulty adjusted to: ${newDifficulty}`;
        this.showNotification(notification, 'info');
    }

    getCurrentQuestionId() {
        const questionElement = document.querySelector('[data-question-id]');
        return questionElement ? questionElement.dataset.questionId : null;
    }

    showNotification(message, type = 'info') {
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} notification-popup`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }

    // Cleanup when leaving practice
    cleanup() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.practice-container')) {
        window.enhancedPracticeManager = new EnhancedPracticeManager();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (window.enhancedPracticeManager) {
                window.enhancedPracticeManager.cleanup();
            }
        });
    }
});

// Export for use in other modules
window.EnhancedPracticeManager = EnhancedPracticeManager;