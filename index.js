// 国际化管理器
class I18nManager {
    constructor() {
        this.currentLang = localStorage.getItem('preferred_language') || 'zh';
        this.translations = {};
        this.init();
    }

    // 初始化
    init() {
        this.loadLanguage(this.currentLang);
        this.applyLanguage();
    }

    // 加载语言包
    loadLanguage(lang) {
        const langMap = {
            'zh': window.I18N_ZH,
            'en': window.I18N_EN
        };
        
        this.translations = langMap[lang] || langMap['zh'];
        this.currentLang = lang;
        localStorage.setItem('preferred_language', lang);
    }

    // 获取翻译
    t(key, params = {}) {
        let text = this.translations[key] || key;
        
        // 替换参数
        Object.keys(params).forEach(param => {
            text = text.replace(`{${param}}`, params[param]);
        });
        
        return text;
    }

    // 应用语言到页面
    applyLanguage() {
        // 遍历所有带有 data-i18n 属性的元素
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // 处理带有 data-i18n-title 的元素（标题属性）
        const titleElements = document.querySelectorAll('[data-i18n-title]');
        titleElements.forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // 更新语言切换按钮状态
        this.updateLanguageSwitcher();
        
        // 触发自定义事件，通知其他组件语言已更改
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: this.currentLang }
        }));
    }

    // 更新语言切换器状态
    updateLanguageSwitcher() {
        const switcher = document.getElementById('languageSwitcher');
        if (switcher) {
            switcher.value = this.currentLang;
        }
    }

    // 切换语言
    switchLanguage(lang) {
        if (lang !== this.currentLang) {
            this.loadLanguage(lang);
            this.applyLanguage();
            
            // 显示切换成功的消息
            const message = lang === 'zh' ? '语言已切换到中文' : 'Language switched to English';
            if (window.showMessage) {
                window.showMessage(message, 'success');
            }
        }
    }

    // 获取当前语言
    getCurrentLanguage() {
        return this.currentLang;
    }
}

// 创建全局实例
window.i18nManager = new I18nManager();

// 语言切换函数
window.switchLanguage = function(lang) {
    window.i18nManager.switchLanguage(lang);
};

console.log('✅ I18n module loaded successfully');