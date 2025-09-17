// Progress Charts with Chart.js Integration for Value Enhancement

class ProgressChartManager {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = this.getDefaultConfigs();
        this.colorSchemes = this.getColorSchemes();
        this.init();
    }

    init() {
        // Wait for Chart.js to load
        if (typeof Chart === 'undefined') {
            setTimeout(() => this.init(), 100);
            return;
        }
        
        this.initializeAllCharts();
        this.setupRealtimeUpdates();
    }

    getDefaultConfigs() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: '#4169e1',
                    borderWidth: 1
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        };
    }

    getColorSchemes() {
        return {
            primary: '#4169e1',
            secondary: '#d4a859',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            gradients: {
                primary: 'linear-gradient(135deg, #4169e1, #6c5ce7)',
                success: 'linear-gradient(135deg, #28a745, #20c997)',
                warning: 'linear-gradient(135deg, #ffc107, #fd7e14)'
            }
        };
    }

    async initializeAllCharts() {
        // Initialize accuracy trend chart
        const accuracyCanvas = document.getElementById('accuracy-chart');
        if (accuracyCanvas) {
            await this.initializeAccuracyChart('accuracy-chart');
        }

        // Initialize topic mastery radar chart
        const masteryCanvas = document.getElementById('mastery-chart');
        if (masteryCanvas) {
            await this.initializeTopicMasteryChart('mastery-chart');
        }

        // Initialize prediction chart
        const predictionCanvas = document.getElementById('prediction-chart');
        if (predictionCanvas) {
            await this.initializePredictionChart('prediction-chart');
        }

        // Initialize streak chart
        const streakCanvas = document.getElementById('streak-chart');
        if (streakCanvas) {
            await this.initializeStreakChart('streak-chart');
        }

        // Initialize performance breakdown
        const breakdownCanvas = document.getElementById('performance-breakdown');
        if (breakdownCanvas) {
            await this.initializePerformanceBreakdown('performance-breakdown');
        }
    }

    async initializeAccuracyChart(canvasId) {
        try {
            const progressData = await this.fetchProgressData();
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            const gradientFill = ctx.createLinearGradient(0, 0, 0, 400);
            gradientFill.addColorStop(0, 'rgba(65, 105, 225, 0.3)');
            gradientFill.addColorStop(1, 'rgba(65, 105, 225, 0.05)');

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: progressData.dates || this.generateDateLabels(30),
                    datasets: [{
                        label: 'Accuracy %',
                        data: progressData.accuracy || this.generateSampleData(30, 60, 95),
                        borderColor: this.colorSchemes.primary,
                        backgroundColor: gradientFill,
                        borderWidth: 3,
                        tension: 0.4,
                        pointBackgroundColor: this.colorSchemes.primary,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        fill: true
                    }]
                },
                options: {
                    ...this.chartConfigs,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    }
                }
            });

            this.charts.set(canvasId, chart);
        } catch (error) {
            console.error('Error initializing accuracy chart:', error);
            this.showChartError(canvasId, 'Failed to load accuracy data');
        }
    }

    async initializeTopicMasteryChart(canvasId) {
        try {
            const masteryData = await this.fetchTopicMasteryData();
            const ctx = document.getElementById(canvasId).getContext('2d');

            const chart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: masteryData.topics || ['Quantitative', 'Verbal', 'Analytical', 'Integrated', 'Critical Thinking'],
                    datasets: [{
                        label: 'Current Mastery',
                        data: masteryData.current || [75, 85, 60, 70, 80],
                        borderColor: this.colorSchemes.primary,
                        backgroundColor: 'rgba(65, 105, 225, 0.2)',
                        borderWidth: 2,
                        pointBackgroundColor: this.colorSchemes.primary,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2
                    }, {
                        label: 'Target Mastery',
                        data: masteryData.target || [90, 90, 85, 88, 90],
                        borderColor: this.colorSchemes.secondary,
                        backgroundColor: 'rgba(212, 168, 89, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointBackgroundColor: this.colorSchemes.secondary,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    ...this.chartConfigs,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            pointLabels: {
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                display: false
                            }
                        }
                    }
                }
            });

            this.charts.set(canvasId, chart);
        } catch (error) {
            console.error('Error initializing mastery chart:', error);
            this.showChartError(canvasId, 'Failed to load mastery data');
        }
    }

    async initializePredictionChart(canvasId) {
        try {
            const predictionData = await this.fetchPredictionData();
            const ctx = document.getElementById(canvasId).getContext('2d');

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: predictionData.dates || this.generateFutureDateLabels(60),
                    datasets: [{
                        label: 'Historical Performance',
                        data: predictionData.historical || this.generateSampleData(30, 60, 85),
                        borderColor: this.colorSchemes.primary,
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        borderWidth: 2,
                        tension: 0.4
                    }, {
                        label: 'Projected Performance',
                        data: predictionData.projected || this.generateProjectionData(30, 85, 95),
                        borderColor: this.colorSchemes.success,
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.4
                    }, {
                        label: 'Target Score',
                        data: new Array(60).fill(90),
                        borderColor: this.colorSchemes.secondary,
                        backgroundColor: 'transparent',
                        borderWidth: 1,
                        pointRadius: 0
                    }]
                },
                options: {
                    ...this.chartConfigs,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        ...this.chartConfigs.plugins,
                        annotation: {
                            annotations: {
                                targetLine: {
                                    type: 'line',
                                    yMin: 90,
                                    yMax: 90,
                                    borderColor: this.colorSchemes.secondary,
                                    borderWidth: 2,
                                    label: {
                                        content: 'Target Score',
                                        enabled: true,
                                        position: 'end'
                                    }
                                }
                            }
                        }
                    }
                }
            });

            this.charts.set(canvasId, chart);
        } catch (error) {
            console.error('Error initializing prediction chart:', error);
            this.showChartError(canvasId, 'Failed to load prediction data');
        }
    }

    async initializeStreakChart(canvasId) {
        try {
            const streakData = await this.fetchStreakData();
            const ctx = document.getElementById(canvasId).getContext('2d');

            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: streakData.dates || this.generateDateLabels(30),
                    datasets: [{
                        label: 'Daily Activity',
                        data: streakData.activity || this.generateStreakData(30),
                        backgroundColor: streakData.activity?.map(val => 
                            val > 0 ? this.colorSchemes.success : 'rgba(220, 53, 69, 0.3)'
                        ) || [],
                        borderColor: streakData.activity?.map(val => 
                            val > 0 ? this.colorSchemes.success : '#dc3545'
                        ) || [],
                        borderWidth: 1
                    }]
                },
                options: {
                    ...this.chartConfigs,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value + ' questions';
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });

            this.charts.set(canvasId, chart);
        } catch (error) {
            console.error('Error initializing streak chart:', error);
            this.showChartError(canvasId, 'Failed to load streak data');
        }
    }

    async initializePerformanceBreakdown(canvasId) {
        try {
            const breakdownData = await this.fetchPerformanceBreakdown();
            const ctx = document.getElementById(canvasId).getContext('2d');

            const chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: breakdownData.labels || ['Correct', 'Incorrect', 'Skipped'],
                    datasets: [{
                        data: breakdownData.values || [75, 20, 5],
                        backgroundColor: [
                            this.colorSchemes.success,
                            this.colorSchemes.danger,
                            this.colorSchemes.warning
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    ...this.chartConfigs,
                    cutout: '60%',
                    plugins: {
                        ...this.chartConfigs.plugins,
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        }
                    }
                }
            });

            this.charts.set(canvasId, chart);
        } catch (error) {
            console.error('Error initializing breakdown chart:', error);
            this.showChartError(canvasId, 'Failed to load breakdown data');
        }
    }

    setupRealtimeUpdates() {
        // Update charts every 5 minutes
        setInterval(() => {
            this.updateChartsRealTime();
        }, 300000);

        // Update when user completes questions
        window.addEventListener('questionCompleted', () => {
            setTimeout(() => this.updateChartsRealTime(), 1000);
        });
    }

    async updateChartsRealTime() {
        try {
            const updates = await this.fetchLatestData();
            
            this.charts.forEach((chart, chartId) => {
                if (updates[chartId]) {
                    this.updateChart(chart, updates[chartId]);
                }
            });
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    updateChart(chart, newData) {
        if (chart.data.datasets[0]) {
            chart.data.datasets[0].data = newData.data;
            if (newData.labels) {
                chart.data.labels = newData.labels;
            }
            chart.update('smooth');
        }
    }

    // API Data Fetching Methods
    async fetchProgressData() {
        try {
            const response = await fetch('/api/progress-data');
            if (!response.ok) throw new Error('Failed to fetch progress data');
            return await response.json();
        } catch (error) {
            console.log('Using sample progress data');
            return {
                dates: this.generateDateLabels(30),
                accuracy: this.generateSampleData(30, 60, 95)
            };
        }
    }

    async fetchTopicMasteryData() {
        try {
            const response = await fetch('/api/topic-mastery');
            if (!response.ok) throw new Error('Failed to fetch mastery data');
            return await response.json();
        } catch (error) {
            console.log('Using sample mastery data');
            return {
                topics: ['Quantitative', 'Verbal', 'Analytical', 'Integrated', 'Critical Thinking'],
                current: [75, 85, 60, 70, 80],
                target: [90, 90, 85, 88, 90]
            };
        }
    }

    async fetchPredictionData() {
        try {
            const response = await fetch('/api/prediction-data');
            if (!response.ok) throw new Error('Failed to fetch prediction data');
            return await response.json();
        } catch (error) {
            console.log('Using sample prediction data');
            return {
                dates: this.generateFutureDateLabels(60),
                historical: this.generateSampleData(30, 60, 85),
                projected: this.generateProjectionData(30, 85, 95)
            };
        }
    }

    async fetchStreakData() {
        try {
            const response = await fetch('/api/streak-data');
            if (!response.ok) throw new Error('Failed to fetch streak data');
            return await response.json();
        } catch (error) {
            console.log('Using sample streak data');
            return {
                dates: this.generateDateLabels(30),
                activity: this.generateStreakData(30)
            };
        }
    }

    async fetchPerformanceBreakdown() {
        try {
            const response = await fetch('/api/performance-breakdown');
            if (!response.ok) throw new Error('Failed to fetch breakdown data');
            return await response.json();
        } catch (error) {
            console.log('Using sample breakdown data');
            return {
                labels: ['Correct', 'Incorrect', 'Skipped'],
                values: [75, 20, 5]
            };
        }
    }

    async fetchLatestData() {
        try {
            const response = await fetch('/api/chart-updates');
            if (!response.ok) throw new Error('Failed to fetch updates');
            return await response.json();
        } catch (error) {
            console.log('Chart update failed');
            return {};
        }
    }

    // Utility Methods for Sample Data
    generateDateLabels(days) {
        const labels = [];
        const today = new Date();
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }
        return labels;
    }

    generateFutureDateLabels(days) {
        const labels = [];
        const today = new Date();
        for (let i = -30; i < days - 30; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() + i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }
        return labels;
    }

    generateSampleData(count, min, max) {
        const data = [];
        let current = (min + max) / 2;
        for (let i = 0; i < count; i++) {
            current += (Math.random() - 0.5) * 10;
            current = Math.max(min, Math.min(max, current));
            data.push(Math.round(current));
        }
        return data;
    }

    generateProjectionData(count, start, target) {
        const data = [];
        const increment = (target - start) / count;
        for (let i = 0; i < count; i++) {
            const projected = start + (increment * i) + (Math.random() - 0.5) * 5;
            data.push(Math.round(Math.max(start, Math.min(target + 10, projected))));
        }
        return data;
    }

    generateStreakData(days) {
        const data = [];
        for (let i = 0; i < days; i++) {
            // 80% chance of activity, 0-20 questions per day
            data.push(Math.random() > 0.2 ? Math.floor(Math.random() * 20) : 0);
        }
        return data;
    }

    showChartError(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (canvas) {
            const container = canvas.parentElement;
            container.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${message}</p>
                    <button class="btn btn-sm btn-primary" onclick="location.reload()">Retry</button>
                </div>
            `;
        }
    }

    // Public API
    getChart(chartId) {
        return this.charts.get(chartId);
    }

    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('[id$="-chart"]')) {
        window.progressChartManager = new ProgressChartManager();
    }
});

// Export for use in other modules
window.ProgressChartManager = ProgressChartManager;