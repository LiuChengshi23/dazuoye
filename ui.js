// ==============================================
// UI 核心工具库 - 严格保留原始结构，仅修复功能
// 不修改原有侧边栏DOM，只补充缺失功能
// ==============================================

// 保留原始函数引用
const originalLoadSidebar = window.loadSidebar;

/**
 * 增强版侧边栏加载（添加语言切换器，避免递归）
 */
function loadSidebarWithI18n() {
    try {
        console.log('🔧 开始加载侧边栏（增强版）...');
        
        // 先执行原始侧边栏加载（如果存在）
        if (typeof originalLoadSidebar === 'function') {
            originalLoadSidebar();
        } else {
            // 如果原始函数不存在，执行基础侧边栏加载
            loadBaseSidebar();
        }
        
        // 在侧边栏添加语言切换器（如果不存在）
        addLanguageSwitcherToSidebar();
        
        console.log('✅ 增强版侧边栏加载完成');
    } catch (error) {
        console.error('❌ 增强版侧边栏加载失败:', error);
        // 降级到基础侧边栏
        loadBaseSidebar();
    }
}

/**
 * 基础侧边栏加载（无递归风险）
 */
function loadBaseSidebar() {
    try {
        console.log('🔧 执行基础侧边栏加载...');
        
        // 优先使用页面已有的侧边栏容器
        let sidebarContainer = document.querySelector('.sidebar');
        if (!sidebarContainer) {
            // 仅在完全没有侧边栏时才创建
            sidebarContainer = document.createElement('div');
            sidebarContainer.className = 'sidebar';
            // 基础侧边栏HTML结构
            sidebarContainer.innerHTML = `
                <div class="sidebar-header">
                    <h1 data-i18n="sidebar.system">服务器系统</h1>
                </div>
                <div class="sidebar-nav">
                    <a href="index.html" class="sidebar-nav-link">
                        <div class="sidebar-item">
                            <i class="fas fa-server"></i>
                            <span data-i18n="sidebar.server_monitor">服务器监控</span>
                        </div>
                    </a>
                    <a href="dashboard.html" class="sidebar-nav-link">
                        <div class="sidebar-item">
                            <i class="fas fa-chart-pie"></i>
                            <span data-i18n="sidebar.dashboard">监控大屏</span>
                        </div>
                    </a>
                    <a href="index.html" class="sidebar-nav-link">
                        <div class="sidebar-item">
                            <i class="fas fa-desktop"></i>
                            <span data-i18n="sidebar.host_management">主机管理</span>
                        </div>
                    </a>
                    <a href="history.html" class="sidebar-nav-link">
                        <div class="sidebar-item">
                            <i class="fas fa-history"></i>
                            <span data-i18n="sidebar.history">历史记录</span>
                        </div>
                    </a>
                    <a href="settings.html" class="sidebar-nav-link">
                        <div class="sidebar-item">
                            <i class="fas fa-cog"></i>
                            <span data-i18n="sidebar.settings">系统设置</span>
                        </div>
                    </a>
                </div>
            `;
            document.body.prepend(sidebarContainer);
            
            // 调整主内容区margin
            const content = document.querySelector('.content');
            if (content) {
                content.style.marginLeft = '260px';
            }
        }

        // 修复菜单高亮
        fixSidebarHighlight();
        console.log('✅ 基础侧边栏加载完成');
    } catch (error) {
        console.error('❌ 基础侧边栏加载失败:', error);
    }
}

/**
 * 修复侧边栏菜单高亮
 */
function fixSidebarHighlight() {
    const currentHref = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.sidebar-nav-link').forEach(link => {
        const sidebarItem = link.querySelector('.sidebar-item');
        if (sidebarItem) {
            if (link.href.includes(currentHref)) {
                sidebarItem.classList.add('active');
            } else {
                sidebarItem.classList.remove('active');
            }
        }
    });
}

/**
 * 添加语言切换器到侧边栏
 */
function addLanguageSwitcherToSidebar() {
    const sidebarNav = document.querySelector('.sidebar-nav');
    if (sidebarNav && !document.querySelector('.sidebar .language-switcher')) {
        const languageSwitcher = createLanguageSwitcher();
        sidebarNav.insertAdjacentHTML('afterend', languageSwitcher);
        
        // 添加语言切换事件监听
        const switcher = document.getElementById('languageSwitcher');
        if (switcher) {
            switcher.addEventListener('change', function() {
                if (window.switchLanguage) {
                    window.switchLanguage(this.value);
                }
            });
            
            // 设置当前语言
            if (window.i18nManager) {
                switcher.value = window.i18nManager.getCurrentLanguage();
            }
        }
    }
}

/**
 * 显示消息提示（适配深色主题，不影响原有页面）
 * @param {string} text - 提示文本
 * @param {string} type - 类型：success/error/warning/info（默认info）
 * @param {number} duration - 显示时长（毫秒，默认3000）
 */
function showMessage(text, type = 'info', duration = 3000) {
    // 移除已存在的提示框，避免重叠
    const existingAlert = document.querySelector('.global-alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // 创建提示框（样式不影响原有页面）
    const alert = document.createElement('div');
    alert.className = `global-alert alert alert-${type}`;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.padding = '15px 20px';
    alert.style.borderRadius = '8px';
    alert.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
    alert.style.transition = 'all 0.3s ease';
    alert.innerHTML = text;

    // 深色主题适配（和你原始页面风格一致）
    switch (type) {
        case 'success':
            alert.style.backgroundColor = 'rgba(34, 197, 94, 0.2)';
            alert.style.border = '1px solid rgba(34, 197, 94, 0.3)';
            alert.style.color = '#4ade80';
            break;
        case 'error':
            alert.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
            alert.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            alert.style.color = '#f87171';
            break;
        case 'warning':
            alert.style.backgroundColor = 'rgba(251, 191, 36, 0.1)';
            alert.style.border = '1px solid rgba(251, 191, 36, 0.3)';
            alert.style.color = '#fbbf24';
            break;
        default: // info
            alert.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
            alert.style.border = '1px solid rgba(59, 130, 246, 0.3)';
            alert.style.color = '#60a5fa';
    }

    document.body.appendChild(alert);
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        setTimeout(() => alert.remove(), 300);
    }, duration);
}

/**
 * 显示加载动画（兼容原始页面的主机列表容器）
 * @param {string} containerId - 容器ID（加载动画将插入到该容器中）
 */
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        // 保留原始加载动画样式（和你初始页面一致）
        container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading" style="margin: 0 auto;"></div>
                <p style="margin-top: 15px; color: #778da9;">加载中...</p>
            </div>
        `;
        // 确保加载动画样式存在（还原原始CSS）
        const style = document.createElement('style');
        style.textContent = `
            .loading {
                width: 40px;
                height: 40px;
                border: 4px solid #415a77;
                border-top: 4px solid #4cc9f0;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * 隐藏加载动画（保留容器原有内容，不覆盖主机列表）
 * @param {string} containerId - 容器ID
 */
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const loadingDiv = container.querySelector('.loading')?.parentNode?.parentNode;
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
}

/**
 * 格式化时间（兼容原始页面的时间显示）
 * @param {string|Date} time - 时间戳/日期字符串/Date对象
 * @returns {string} 格式化后的时间（YYYY-MM-DD HH:MM:SS）
 */
function formatTime(time) {
    if (!time) return '未知时间';
    try {
        const date = typeof time === 'string' ? new Date(time) : time;
        if (isNaN(date.getTime())) return time;
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hour = String(date.getHours()).padStart(2, '0');
        const minute = String(date.getMinutes()).padStart(2, '0');
        const second = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
    } catch (error) {
        console.error('❌ 时间格式化失败:', error);
        return time;
    }
}

/**
 * 验证IP地址格式（辅助主机添加页面）
 * @param {string} ip - 待验证的IP地址
 * @returns {boolean} 是否为合法IP
 */
function isValidIp(ip) {
    const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

/**
 * 验证端口号格式（辅助主机添加页面）
 * @param {number|string} port - 待验证的端口号
 * @returns {boolean} 是否为合法端口
 */
function isValidPort(port) {
    const portNum = parseInt(port);
    return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
}

// ==============================================
// 国际化支持 - 新增功能（不破坏现有系统）
// ==============================================

/**
 * 初始化国际化支持
 */
function initI18n() {
    // 确保语言管理器已加载
    if (window.i18nManager) {
        window.i18nManager.applyLanguage();
    }
}

/**
 * 创建语言切换器（添加到侧边栏）
 */
function createLanguageSwitcher() {
    const currentLang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh';
    
    const switcherHtml = `
        <div class="language-switcher" style="margin-top: auto; padding: 15px 25px; border-top: 1px solid #415a77;">
            <label for="languageSwitcher" style="display: block; margin-bottom: 8px; color: #778da9; font-size: 0.9em;">
                🌐 语言 / Language
            </label>
            <select id="languageSwitcher" class="form-control" style="width: 100%; padding: 8px 12px; background: rgba(13, 27, 42, 0.7); border: 1px solid #415a77; border-radius: 4px; color: #e0e1dd;">
                <option value="zh">中文</option>
                <option value="en">English</option>
            </select>
        </div>
    `;
    
    return switcherHtml;
}

// ==============================================
// 全局导出（保持原始调用方式 + 新增功能）
// ==============================================
window.loadSidebar = loadSidebarWithI18n; // 替换为增强版，避免递归
window.showMessage = showMessage;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatTime = formatTime;
window.isValidIp = isValidIp;
window.isValidPort = isValidPort;

// 导出新增的国际化功能
window.initI18n = initI18n;
window.createLanguageSwitcher = createLanguageSwitcher;
window.fixSidebarHighlight = fixSidebarHighlight;

// ==============================================
// 初始化：DOM加载完成后执行
// ==============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 UI工具库初始化完成（修复递归问题）');
    
    // 初始化国际化
    if (window.i18nManager) {
        window.i18nManager.applyLanguage();
    }
    
    // 如果页面已经有侧边栏，只修复高亮和添加语言切换器
    if (document.querySelector('.sidebar')) {
        fixSidebarHighlight();
        addLanguageSwitcherToSidebar();
        console.log('✅ 已有侧边栏，修复菜单高亮和语言切换器完成');
    }
});