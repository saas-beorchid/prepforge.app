// Social Learning Features Frontend Implementation

class SocialManager {
    constructor() {
        this.apiEndpoints = {
            leaderboard: '/social/leaderboard',
            studyGroups: '/social/study-groups',
            notifications: '/social/api/social-notifications',
            joinGroup: '/social/join-group',
            submitComment: '/social/submit-comment',
            voteComment: '/social/vote-comment'
        };
        this.updateIntervals = new Map();
        this.init();
    }

    init() {
        this.initLeaderboard();
        this.initStudyGroups();
        this.initQuestionDiscussion();
        this.initNotifications();
        this.setupRealtimeUpdates();
    }

    initLeaderboard() {
        const leaderboardContainer = document.querySelector('.leaderboard-container');
        if (!leaderboardContainer) return;

        // Initialize period selector
        const periodSelector = document.getElementById('leaderboard-period');
        if (periodSelector) {
            periodSelector.addEventListener('change', (e) => {
                this.loadLeaderboard(null, e.target.value);
            });
        }

        // Initialize exam type selector
        const examSelector = document.getElementById('leaderboard-exam');
        if (examSelector) {
            examSelector.addEventListener('change', (e) => {
                this.loadLeaderboard(e.target.value, null);
            });
        }

        // Load initial leaderboard
        this.loadLeaderboard();
    }

    async loadLeaderboard(examType = null, period = null) {
        try {
            const currentExam = examType || document.getElementById('leaderboard-exam')?.value || 'GMAT';
            const currentPeriod = period || document.getElementById('leaderboard-period')?.value || 'weekly';
            
            const response = await fetch(`${this.apiEndpoints.leaderboard}/${currentExam}/${currentPeriod}`);
            
            if (!response.ok) {
                throw new Error('Failed to load leaderboard');
            }

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newContent = doc.querySelector('.leaderboard-content');
            
            if (newContent) {
                const container = document.querySelector('.leaderboard-content');
                if (container) {
                    // Animate out old content
                    container.style.opacity = '0';
                    
                    setTimeout(() => {
                        container.innerHTML = newContent.innerHTML;
                        this.animateLeaderboardRankings();
                        container.style.opacity = '1';
                    }, 300);
                }
            }

        } catch (error) {
            console.error('Error loading leaderboard:', error);
            this.showError('Failed to load leaderboard data');
        }
    }

    animateLeaderboardRankings() {
        const rankingItems = document.querySelectorAll('.ranking-item');
        
        rankingItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 50);
        });

        // Highlight current user
        const currentUserItem = document.querySelector('.ranking-item.current-user');
        if (currentUserItem) {
            setTimeout(() => {
                currentUserItem.classList.add('highlight-pulse');
            }, 1000);
        }
    }

    initStudyGroups() {
        // Join group buttons
        const joinButtons = document.querySelectorAll('.join-group-btn');
        joinButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const groupId = e.target.dataset.groupId;
                this.joinStudyGroup(groupId);
            });
        });

        // Create group form
        const createGroupForm = document.getElementById('create-group-form');
        if (createGroupForm) {
            createGroupForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createStudyGroup(new FormData(createGroupForm));
            });
        }

        // Group search functionality
        const groupSearch = document.getElementById('group-search');
        if (groupSearch) {
            groupSearch.addEventListener('input', (e) => {
                this.filterGroups(e.target.value);
            });
        }
    }

    async joinStudyGroup(groupId) {
        try {
            const response = await fetch(`${this.apiEndpoints.joinGroup}/${groupId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ group_id: groupId })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                
                // Update UI to reflect membership
                const joinBtn = document.querySelector(`[data-group-id="${groupId}"]`);
                if (joinBtn) {
                    joinBtn.textContent = 'Joined!';
                    joinBtn.disabled = true;
                    joinBtn.classList.add('btn-success');
                }

                // Redirect to group if specified
                if (result.redirect) {
                    setTimeout(() => {
                        window.location.href = result.redirect;
                    }, 1500);
                }
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error joining group:', error);
            this.showError('Failed to join study group');
        }
    }

    async createStudyGroup(formData) {
        try {
            const data = Object.fromEntries(formData);
            
            const response = await fetch('/social/create-group', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                
                // Show invite code if provided
                if (result.invite_code) {
                    this.showInviteCode(result.invite_code);
                }

                // Redirect to new group
                setTimeout(() => {
                    window.location.href = `/social/group/${result.group_id}`;
                }, 2000);
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error creating group:', error);
            this.showError('Failed to create study group');
        }
    }

    filterGroups(searchTerm) {
        const groupCards = document.querySelectorAll('.group-card');
        const term = searchTerm.toLowerCase();

        groupCards.forEach(card => {
            const groupName = card.querySelector('.group-name')?.textContent.toLowerCase() || '';
            const groupDescription = card.querySelector('.group-description')?.textContent.toLowerCase() || '';
            
            if (groupName.includes(term) || groupDescription.includes(term)) {
                card.style.display = 'block';
                card.classList.add('fade-in');
            } else {
                card.style.display = 'none';
            }
        });
    }

    initStudyGroupChat() {
        const chatContainer = document.querySelector('.group-chat-container');
        if (!chatContainer) return;

        // Initialize WebSocket connection for real-time chat
        this.initWebSocket();

        // Setup message sending
        const messageForm = document.getElementById('chat-message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendChatMessage();
            });
        }

        // Setup typing indicators
        const messageInput = document.getElementById('chat-message-input');
        if (messageInput) {
            let typingTimer;
            messageInput.addEventListener('input', () => {
                this.sendTypingIndicator(true);
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    this.sendTypingIndicator(false);
                }, 1000);
            });
        }
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/group-chat`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                this.initWebSocket();
            }, 3000);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chat_message':
                this.displayChatMessage(data.message);
                break;
            case 'typing_indicator':
                this.updateTypingIndicator(data.user, data.isTyping);
                break;
            case 'user_online':
                this.updateUserOnlineStatus(data.user, true);
                break;
            case 'user_offline':
                this.updateUserOnlineStatus(data.user, false);
                break;
        }
    }

    sendChatMessage() {
        const messageInput = document.getElementById('chat-message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'chat_message',
                message: message,
                group_id: this.getCurrentGroupId()
            }));
            
            messageInput.value = '';
        }
    }

    displayChatMessage(messageData) {
        const chatMessages = document.querySelector('.chat-messages');
        if (!chatMessages) return;

        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        messageElement.innerHTML = `
            <div class="message-header">
                <span class="username">${messageData.username}</span>
                <span class="timestamp">${this.formatTimestamp(messageData.timestamp)}</span>
            </div>
            <div class="message-content">${this.escapeHtml(messageData.content)}</div>
        `;

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Animate new message
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';
        setTimeout(() => {
            messageElement.style.transition = 'all 0.3s ease';
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
        }, 100);
    }

    initQuestionDiscussion(questionId = null) {
        const discussionContainer = document.querySelector('.question-discussion');
        if (!discussionContainer) return;

        this.currentQuestionId = questionId || this.getCurrentQuestionId();

        // Setup comment submission
        const commentForm = document.getElementById('comment-form');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitComment();
            });
        }

        // Setup voting buttons
        this.initCommentVoting();

        // Setup reply functionality
        this.initCommentReplies();
    }

    async submitComment(parentCommentId = null) {
        try {
            const commentText = document.getElementById('comment-text').value.trim();
            
            if (!commentText) {
                this.showError('Please enter a comment');
                return;
            }

            const response = await fetch(this.apiEndpoints.submitComment, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_id: this.currentQuestionId,
                    comment_text: commentText,
                    parent_comment_id: parentCommentId
                })
            });

            const result = await response.json();

            if (result.success) {
                this.addCommentToDOM(result.comment, parentCommentId);
                document.getElementById('comment-text').value = '';
                this.showSuccess('Comment added successfully!');
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error submitting comment:', error);
            this.showError('Failed to submit comment');
        }
    }

    addCommentToDOM(commentData, parentCommentId = null) {
        const commentElement = document.createElement('div');
        commentElement.className = 'comment-item';
        commentElement.dataset.commentId = commentData.id;
        
        commentElement.innerHTML = `
            <div class="comment-header">
                <span class="username">${commentData.username}</span>
                <span class="timestamp">${commentData.created_at}</span>
            </div>
            <div class="comment-content">${this.escapeHtml(commentData.text)}</div>
            <div class="comment-actions">
                <button class="btn btn-sm btn-outline-primary vote-btn" data-comment-id="${commentData.id}">
                    <i class="fas fa-thumbs-up"></i> Helpful (${commentData.helpful_votes})
                </button>
                <button class="btn btn-sm btn-outline-secondary reply-btn" data-comment-id="${commentData.id}">
                    <i class="fas fa-reply"></i> Reply
                </button>
            </div>
            <div class="replies-container"></div>
        `;

        // Add to appropriate container
        if (parentCommentId) {
            const parentComment = document.querySelector(`[data-comment-id="${parentCommentId}"]`);
            const repliesContainer = parentComment.querySelector('.replies-container');
            repliesContainer.appendChild(commentElement);
        } else {
            const commentsContainer = document.querySelector('.comments-container');
            commentsContainer.appendChild(commentElement);
        }

        // Initialize voting for new comment
        this.initCommentVoting(commentElement);

        // Animate in
        commentElement.style.opacity = '0';
        commentElement.style.transform = 'translateY(20px)';
        setTimeout(() => {
            commentElement.style.transition = 'all 0.3s ease';
            commentElement.style.opacity = '1';
            commentElement.style.transform = 'translateY(0)';
        }, 100);
    }

    initCommentVoting(container = document) {
        const voteButtons = container.querySelectorAll('.vote-btn');
        
        voteButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const commentId = btn.dataset.commentId;
                await this.voteOnComment(commentId, btn);
            });
        });
    }

    async voteOnComment(commentId, buttonElement) {
        try {
            const response = await fetch(`${this.apiEndpoints.voteComment}/${commentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                // Update vote count in UI
                const voteCount = buttonElement.querySelector('.vote-count') || buttonElement;
                voteCount.innerHTML = `<i class="fas fa-thumbs-up"></i> Helpful (${result.new_vote_count})`;
                
                // Add visual feedback
                buttonElement.classList.add('voted');
                buttonElement.disabled = true;
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error voting on comment:', error);
            this.showError('Failed to vote on comment');
        }
    }

    initCommentReplies() {
        const replyButtons = document.querySelectorAll('.reply-btn');
        
        replyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const commentId = btn.dataset.commentId;
                this.showReplyForm(commentId);
            });
        });
    }

    showReplyForm(commentId) {
        // Remove any existing reply forms
        const existingForms = document.querySelectorAll('.reply-form');
        existingForms.forEach(form => form.remove());

        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        const replyForm = document.createElement('div');
        replyForm.className = 'reply-form';
        replyForm.innerHTML = `
            <div class="form-group">
                <textarea class="form-control" placeholder="Write your reply..." rows="3"></textarea>
            </div>
            <div class="form-actions">
                <button class="btn btn-primary btn-sm submit-reply">Post Reply</button>
                <button class="btn btn-secondary btn-sm cancel-reply">Cancel</button>
            </div>
        `;

        commentElement.appendChild(replyForm);

        // Handle form actions
        replyForm.querySelector('.submit-reply').addEventListener('click', () => {
            const replyText = replyForm.querySelector('textarea').value.trim();
            if (replyText) {
                this.submitComment(commentId);
                replyForm.remove();
            }
        });

        replyForm.querySelector('.cancel-reply').addEventListener('click', () => {
            replyForm.remove();
        });
    }

    initNotifications() {
        this.updateSocialNotifications();
        
        // Update notifications every 30 seconds
        this.updateIntervals.set('notifications', setInterval(() => {
            this.updateSocialNotifications();
        }, 30000));
    }

    async updateSocialNotifications() {
        try {
            const response = await fetch(this.apiEndpoints.notifications);
            const result = await response.json();

            if (result.success) {
                this.displayNotifications(result.notifications);
                this.updateNotificationBadge(result.count);
            }
        } catch (error) {
            console.error('Error updating notifications:', error);
        }
    }

    displayNotifications(notifications) {
        const notificationContainer = document.querySelector('.social-notifications');
        if (!notificationContainer) return;

        notificationContainer.innerHTML = '';

        notifications.forEach(notification => {
            const notificationElement = document.createElement('div');
            notificationElement.className = 'notification-item';
            notificationElement.innerHTML = `
                <div class="notification-content">
                    <span class="notification-message">${notification.message}</span>
                    <span class="notification-time">${notification.time}</span>
                </div>
            `;
            notificationContainer.appendChild(notificationElement);
        });
    }

    updateNotificationBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    setupRealtimeUpdates() {
        // Update leaderboard every 5 minutes
        this.updateIntervals.set('leaderboard', setInterval(() => {
            if (document.querySelector('.leaderboard-container')) {
                this.loadLeaderboard();
            }
        }, 300000));
    }

    // Utility methods
    getCurrentGroupId() {
        const groupElement = document.querySelector('[data-group-id]');
        return groupElement ? groupElement.dataset.groupId : null;
    }

    getCurrentQuestionId() {
        const questionElement = document.querySelector('[data-question-id]');
        return questionElement ? questionElement.dataset.questionId : null;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    showError(message) {
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    showInviteCode(code) {
        const modal = document.createElement('div');
        modal.className = 'invite-code-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h4>Group Created Successfully!</h4>
                <p>Share this invite code with others:</p>
                <div class="invite-code">${code}</div>
                <button class="btn btn-primary" onclick="this.closest('.invite-code-modal').remove()">
                    Got it!
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Cleanup method
    destroy() {
        this.updateIntervals.forEach((interval) => {
            clearInterval(interval);
        });
        this.updateIntervals.clear();

        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.social-container, .leaderboard-container, .study-groups-container, .question-discussion')) {
        window.socialManager = new SocialManager();
    }
});

// Export for use in other modules
window.SocialManager = SocialManager;