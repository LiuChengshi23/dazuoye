// API配置 - 使用服务器IP
const API_BASE = 'http://192.168.80.131:5000/api';

console.log('🚀 API模块开始加载...');

// 检查API是否可用
async function checkAPI() {
    try {
        const response = await fetch('http://192.168.80.131:5000/');
        console.log('✅ 后端服务可用:', response.status);
        return true;
    } catch (error) {
        console.error('❌ 后端服务不可用:', error);
        return false;
    }
}

// 通用请求函数
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE}${endpoint}`;
        console.log(`📡 API请求: ${url}`);
        
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        const response = await fetch(url, config);
        console.log('响应状态:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('响应错误:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        console.log('响应数据:', result);
        return result;
    } catch (error) {
        console.error('❌ API请求失败:', error);
        throw error;
    }
}

// 主机管理API
const hostsAPI = {
    // 获取主机列表
    async getHosts() {
        return await apiRequest('/hosts');
    },

    // 添加主机
    async addHost(hostData) {
        return await apiRequest('/hosts', {
            method: 'POST',
            body: hostData
        });
    },

    // 删除主机
    async deleteHost(ip) {
        return await apiRequest(`/hosts/${ip}`, {
            method: 'DELETE'
        });
    },

    // 刷新数据
    async refreshMetrics() {
        return await apiRequest('/refresh', {
            method: 'POST'
        });
    }
};

// 监控数据API
const metricsAPI = {
    // 获取所有监控数据
    async getMetrics() {
        return await apiRequest('/metrics');
    },

    // 健康检查
    async healthCheck() {
        return await apiRequest('/health');
    }
};

// 导出到全局作用域
window.hostsAPI = hostsAPI;
window.metricsAPI = metricsAPI;

console.log('✅ API模块加载完成');
console.log('hostsAPI 类型:', typeof hostsAPI);
console.log('metricsAPI 类型:', typeof metricsAPI);

// 立即检查API可用性
checkAPI();