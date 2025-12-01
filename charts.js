// 图表管理
class ChartManager {
    constructor() {
        this.charts = new Map();
    }

    // 初始化CPU图表
    initCpuChart(containerId) {
        const canvas = document.getElementById(containerId);
        if (!canvas) {
            console.error('找不到图表容器:', containerId);
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'CPU 使用率 (%)',
                        color: '#e0e1dd',
                        font: { size: 14 }
                    },
                    legend: {
                        labels: { color: '#e0e1dd' }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(65, 90, 119, 0.3)' },
                        ticks: { color: '#a8b5c5' }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(65, 90, 119, 0.3)' },
                        ticks: { color: '#a8b5c5' }
                    }
                }
            }
        });

        this.charts.set(containerId, chart);
        return chart;
    }

    // 初始化内存图表
    initMemoryChart(containerId) {
        const canvas = document.getElementById(containerId);
        if (!canvas) {
            console.error('找不到图表容器:', containerId);
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '内存使用率 (%)',
                        color: '#e0e1dd',
                        font: { size: 14 }
                    },
                    legend: {
                        labels: { color: '#e0e1dd' }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(65, 90, 119, 0.3)' },
                        ticks: { color: '#a8b5c5' }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(65, 90, 119, 0.3)' },
                        ticks: { color: '#a8b5c5' }
                    }
                }
            }
        });

        this.charts.set(containerId, chart);
        return chart;
    }

    // 更新图表数据
    updateCharts(metrics) {
        this.updateCpuChart(metrics);
        this.updateMemoryChart(metrics);
    }

    // 更新CPU图表
    updateCpuChart(metrics) {
        const chart = this.charts.get('cpuChart');
        if (!chart) return;

        const datasets = [];
        const colors = ['#4361ee', '#4cc9f0', '#f72585', '#b5179e', '#7209b7', '#3a0ca3'];
        
        let colorIndex = 0;
        for (const [ip, data] of Object.entries(metrics)) {
            const cpuData = data.cpu || [];
            datasets.push({
                label: ip,
                data: cpuData,
                borderColor: colors[colorIndex % colors.length],
                backgroundColor: colors[colorIndex % colors.length] + '20',
                borderWidth: 2,
                tension: 0.4,
                fill: false
            });
            colorIndex++;
        }

        const dataLength = datasets.length > 0 ? (datasets[0].data.length || 0) : 0;
        const labels = Array.from({length: dataLength}, (_, i) => {
            return `点 ${i + 1}`;
        });

        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
    }

    // 更新内存图表
    updateMemoryChart(metrics) {
        const chart = this.charts.get('memoryChart');
        if (!chart) return;

        const datasets = [];
        const colors = ['#f72585', '#b5179e', '#4361ee', '#4cc9f0', '#7209b7', '#3a0ca3'];
        
        let colorIndex = 0;
        for (const [ip, data] of Object.entries(metrics)) {
            const memoryData = data.memory || [];
            datasets.push({
                label: ip,
                data: memoryData,
                borderColor: colors[colorIndex % colors.length],
                backgroundColor: colors[colorIndex % colors.length] + '20',
                borderWidth: 2,
                tension: 0.4,
                fill: false
            });
            colorIndex++;
        }

        const dataLength = datasets.length > 0 ? (datasets[0].data.length || 0) : 0;
        const labels = Array.from({length: dataLength}, (_, i) => {
            return `点 ${i + 1}`;
        });

        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
    }

    // 销毁所有图表
    destroy() {
        for (const chart of this.charts.values()) {
            chart.destroy();
        }
        this.charts.clear();
    }
}

// 创建全局图表管理器
window.chartManager = new ChartManager();