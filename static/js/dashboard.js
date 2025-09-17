// Dashboard Interactive Features and Enhanced Animations

document.addEventListener('DOMContentLoaded', function() {
    initDashboardAnimations();
    initExamCardInteractions();
    initProgressTracking();
    initRealtimeUpdates();
    initStatisticsCounters();
    initQuickActionsMenu();
});

// Initialize dashboard page animations
function initDashboardAnimations() {
    // Stagger animation for exam cards
    const examCards = document.querySelectorAll('.exam-card');
    examCards.forEach((card, index) => {
        card.classList.add('fade-in-up');
        setTimeout(() => {
            card.classList.add('visible');
        }, 100 * index);
    });
    
    // Statistics cards animation
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.animationDelay = `${0.2 + (index * 0.1)}s`;
        card.classList.add('slide-in-left');
    });
    
    // Welcome message typewriter effect
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.classList.add('typewriter');
    }
}

// Enhanced exam card interactions
function initExamCardInteractions() {
    const examCards = document.querySelectorAll('.exam-card');
    
    examCards.forEach(card => {
        const examType = card.dataset.examType;
        
        // Enhanced hover effects
        card.addEventListener('mouseenter', function() {
            this.classList.add('card-hovered');
            
            // Show additional info overlay
            const overlay = this.querySelector('.card-overlay');
            if (overlay) {
                overlay.style.opacity = '1';
                overlay.style.transform = 'translateY(0)';
            }
            
            // Animate progress bars
            const progressBars = this.querySelectorAll('.progress-bar');
            progressBars.forEach(bar => {
                const width = bar.dataset.width || '0%';
                bar.style.width = width;
            });
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('card-hovered');
            
            const overlay = this.querySelector('.card-overlay');
            if (overlay) {
                overlay.style.opacity = '0';
                overlay.style.transform = 'translateY(10px)';
            }
        });
        
        // Click animation and navigation
        card.addEventListener('click', function(e) {
            if (e.target.closest('.btn, .dropdown')) return;
            
            // Add click animation
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Navigate to practice
            setTimeout(() => {
                window.location.href = `/practice/${examType}`;
            }, 200);
        });
        
        // Add ripple effect
        card.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
    });
    
    // Quick action buttons
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const action = this.dataset.action;
            const examType = this.closest('.exam-card').dataset.examType;
            handleQuickAction(action, examType);
        });
    });
}

// Create ripple effect for card clicks
function createRippleEffect(event, element) {
    const ripple = document.createElement('div');
    ripple.className = 'ripple-effect';
    
    const rect = element.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        pointer-events: none;
        transform: scale(0);
        animation: ripple 0.6s linear;
        left: ${x - 10}px;
        top: ${y - 10}px;
        width: 20px;
        height: 20px;
    `;
    
    element.style.position = 'relative';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Handle quick actions
function handleQuickAction(action, examType) {
    switch (action) {
        case 'practice':
            window.location.href = `/practice/${examType}`;
            break;
        case 'analytics':
            showAnalyticsModal(examType);
            break;
        case 'study-plan':
            showStudyPlanModal(examType);
            break;
        case 'leaderboard':
            showLeaderboardModal(examType);
            break;
        default:
            console.log(`Unknown action: ${action}`);
    }
}

// Progress tracking and updates
function initProgressTracking() {
    // Update progress indicators
    updateProgressBars();
    
    // Streak tracking
    updateStreakDisplay();
    
    // Achievement checking
    checkForNewAchievements();
    
    // Real-time progress updates
    setInterval(updateProgressBars, 30000); // Update every 30 seconds
}

function updateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar-animated');
    
    progressBars.forEach(bar => {
        const targetWidth = bar.dataset.progress || '0';
        const currentWidth = parseInt(bar.style.width) || 0;
        
        if (currentWidth !== parseInt(targetWidth)) {
            animateProgressBar(bar, currentWidth, parseInt(targetWidth));
        }
    });
}

function animateProgressBar(bar, from, to) {
    const duration = 1000;
    const steps = 60;
    const stepSize = (to - from) / steps;
    let current = from;
    let step = 0;
    
    const animate = () => {
        if (step < steps) {
            current += stepSize;
            bar.style.width = `${current}%`;
            step++;
            requestAnimationFrame(animate);
        } else {
            bar.style.width = `${to}%`;
        }
    };
    
    animate();
}

// Statistics counters animation
function initStatisticsCounters() {
    const counters = document.querySelectorAll('.stat-counter');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

function animateCounter(element) {
    const target = parseInt(element.dataset.count) || 0;
    const duration = 2000;
    const steps = 60;
    const stepSize = target / steps;
    let current = 0;
    let step = 0;
    
    element.classList.add('animated');
    
    const animate = () => {
        if (step < steps) {
            current += stepSize;
            element.textContent = Math.floor(current);
            step++;
            requestAnimationFrame(animate);
        } else {
            element.textContent = target;
        }
    };
    
    animate();
}

// Real-time updates
function initRealtimeUpdates() {
    // Check for updates every minute
    setInterval(checkForUpdates, 60000);
    
    // Initial check
    setTimeout(checkForUpdates, 2000);
}

function checkForUpdates() {
    // Check for new achievements
    fetch('/api/check-achievements', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.new_achievements) {
            data.new_achievements.forEach(achievement => {
                showAchievementNotification(achievement);
            });
        }
    })
    .catch(error => {
        console.log('Update check failed:', error);
    });
    
    // Update streak information
    updateStreakDisplay();
}

function updateStreakDisplay() {
    const streakElement = document.querySelector('.streak-counter');
    if (streakElement) {
        fetch('/api/current-streak')
        .then(response => response.json())
        .then(data => {
            if (data.streak !== undefined) {
                const currentStreak = parseInt(streakElement.textContent) || 0;
                if (data.streak > currentStreak) {
                    animateStreakUpdate(streakElement, data.streak);
                }
            }
        })
        .catch(error => {
            console.log('Streak update failed:', error);
        });
    }
}

function animateStreakUpdate(element, newStreak) {
    element.classList.add('streak-update');
    element.textContent = newStreak;
    
    // Add celebration effect for milestone streaks
    if (newStreak > 0 && newStreak % 7 === 0) {
        celebrateStreak(newStreak);
    }
    
    setTimeout(() => {
        element.classList.remove('streak-update');
    }, 1000);
}

// Achievement checking
function checkForNewAchievements() {
    // This would typically be called after completing questions
    // For now, it's a placeholder for the achievement system
    const achievements = JSON.parse(localStorage.getItem('pending_achievements') || '[]');
    
    achievements.forEach(achievement => {
        showAchievementNotification(achievement);
    });
    
    // Clear pending achievements
    localStorage.removeItem('pending_achievements');
}

// Quick actions menu
function initQuickActionsMenu() {
    const quickActionsBtn = document.querySelector('.quick-actions-btn');
    const quickActionsMenu = document.querySelector('.quick-actions-menu');
    
    if (quickActionsBtn && quickActionsMenu) {
        quickActionsBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleQuickActionsMenu();
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!quickActionsMenu.contains(e.target)) {
                closeQuickActionsMenu();
            }
        });
    }
}

function toggleQuickActionsMenu() {
    const menu = document.querySelector('.quick-actions-menu');
    if (menu.classList.contains('show')) {
        closeQuickActionsMenu();
    } else {
        openQuickActionsMenu();
    }
}

function openQuickActionsMenu() {
    const menu = document.querySelector('.quick-actions-menu');
    menu.classList.add('show');
    menu.style.animation = 'quickMenuSlideIn 0.3s ease-out forwards';
}

function closeQuickActionsMenu() {
    const menu = document.querySelector('.quick-actions-menu');
    menu.style.animation = 'quickMenuSlideOut 0.3s ease-in forwards';
    setTimeout(() => {
        menu.classList.remove('show');
    }, 300);
}

// Modal Functions
function showAnalyticsModal(examType) {
    const modal = createModal('analytics-modal', 'Performance Analytics', `
        <div class="analytics-content">
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading your performance data...</p>
            </div>
        </div>
    `);
    
    // Load analytics data
    loadAnalyticsData(examType, modal);
}

function showStudyPlanModal(examType) {
    const modal = createModal('study-plan-modal', 'Study Plan', `
        <div class="study-plan-content">
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Creating your personalized study plan...</p>
            </div>
        </div>
    `);
    
    // Load study plan data
    loadStudyPlanData(examType, modal);
}

function showLeaderboardModal(examType) {
    const modal = createModal('leaderboard-modal', 'Leaderboard', `
        <div class="leaderboard-content">
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading leaderboard data...</p>
            </div>
        </div>
    `);
    
    // Load leaderboard data
    loadLeaderboardData(examType, modal);
}

function createModal(id, title, content) {
    // Remove existing modal if present
    const existingModal = document.getElementById(id);
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = id;
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal with animation
    setTimeout(() => {
        modal.classList.add('show');
        modal.style.display = 'block';
    }, 100);
    
    // Handle close button
    modal.querySelector('.btn-close').addEventListener('click', () => {
        closeModal(modal);
    });
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(modal);
        }
    });
    
    return modal;
}

function closeModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        modal.remove();
    }, 300);
}

// Data loading functions
function loadAnalyticsData(examType, modal) {
    fetch(`/api/analytics/${examType}`)
    .then(response => response.json())
    .then(data => {
        const content = modal.querySelector('.analytics-content');
        content.innerHTML = generateAnalyticsHTML(data);
        
        // Initialize charts if needed
        initAnalyticsCharts(data);
    })
    .catch(error => {
        const content = modal.querySelector('.analytics-content');
        content.innerHTML = '<p class="error-message">Failed to load analytics data. Please try again later.</p>';
    });
}

function loadStudyPlanData(examType, modal) {
    fetch(`/api/study-plan/${examType}`)
    .then(response => response.json())
    .then(data => {
        const content = modal.querySelector('.study-plan-content');
        content.innerHTML = generateStudyPlanHTML(data);
    })
    .catch(error => {
        const content = modal.querySelector('.study-plan-content');
        content.innerHTML = '<p class="error-message">Failed to load study plan. Please try again later.</p>';
    });
}

function loadLeaderboardData(examType, modal) {
    fetch(`/api/leaderboard/${examType}`)
    .then(response => response.json())
    .then(data => {
        const content = modal.querySelector('.leaderboard-content');
        content.innerHTML = generateLeaderboardHTML(data);
    })
    .catch(error => {
        const content = modal.querySelector('.leaderboard-content');
        content.innerHTML = '<p class="error-message">Failed to load leaderboard. Please try again later.</p>';
    });
}

// HTML generation functions
function generateAnalyticsHTML(data) {
    return `
        <div class="row">
            <div class="col-md-6">
                <div class="stat-card">
                    <h6>Overall Accuracy</h6>
                    <div class="stat-value">${data.accuracy || 0}%</div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="stat-card">
                    <h6>Questions Answered</h6>
                    <div class="stat-value">${data.total_questions || 0}</div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="stat-card">
                    <h6>Average Time</h6>
                    <div class="stat-value">${data.avg_time || 0}s</div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="stat-card">
                    <h6>Streak</h6>
                    <div class="stat-value">${data.streak || 0} days</div>
                </div>
            </div>
        </div>
        <div class="mt-4">
            <h6>Performance Trends</h6>
            <canvas id="performance-chart" width="400" height="200"></canvas>
        </div>
    `;
}

function generateStudyPlanHTML(data) {
    if (!data.study_plan) {
        return `
            <div class="text-center">
                <p>No active study plan found.</p>
                <button class="btn btn-primary" onclick="createStudyPlan('${data.exam_type}')">
                    Create Study Plan
                </button>
            </div>
        `;
    }
    
    return `
        <div class="study-plan-overview">
            <h6>Your Study Plan for ${data.exam_type}</h6>
            <div class="plan-progress">
                <div class="progress">
                    <div class="progress-bar" style="width: ${data.progress || 0}%"></div>
                </div>
                <p>${data.progress || 0}% Complete</p>
            </div>
            <div class="next-session">
                <h6>Next Study Session</h6>
                <p>${data.next_session || 'No sessions scheduled'}</p>
            </div>
        </div>
    `;
}

function generateLeaderboardHTML(data) {
    if (!data.rankings || data.rankings.length === 0) {
        return '<p class="text-center">No leaderboard data available yet.</p>';
    }
    
    let html = '<div class="leaderboard-list">';
    
    data.rankings.forEach((user, index) => {
        html += `
            <div class="leaderboard-item ${index < 3 ? 'top-3' : ''}">
                <div class="rank">#${index + 1}</div>
                <div class="user-info">
                    <div class="username">${user.name || 'Anonymous'}</div>
                    <div class="score">${user.score} points</div>
                </div>
                ${index < 3 ? `<div class="medal medal-${index + 1}">🏆</div>` : ''}
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// Utility functions
function initAnalyticsCharts(data) {
    // This would initialize charts using Chart.js or similar
    // For now, it's a placeholder
    console.log('Initializing analytics charts with data:', data);
}

function createStudyPlan(examType) {
    // Redirect to study plan creation page
    window.location.href = `/study-plan/create/${examType}`;
}

// CSS animations for the quick menu
const style = document.createElement('style');
style.textContent = `
    @keyframes quickMenuSlideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes quickMenuSlideOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .streak-update {
        animation: streakPulse 1s ease-in-out;
    }
    
    @keyframes streakPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); color: #d4a859; }
    }
`;

document.head.appendChild(style);