// 通用函数和事件处理
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有下拉菜单
    initializeDropdowns();
    
    // 初始化所有表单验证
    initializeFormValidation();
    
    // 添加表格排序功能
    initializeTableSort();
    
    // 添加响应式导航菜单
    initializeResponsiveNav();
    
    if (document.getElementById('password-form')) {
        validatePasswordForm();
    }
});

// 下拉菜单初始化
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.preventDefault();
            const menu = this.nextElementSibling;
            menu.classList.toggle('show');
        });
    });
}

// 表单验证
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

// 表格排序
function initializeTableSort() {
    const tables = document.querySelectorAll('.table-sortable');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                sortTable(table, Array.from(headers).indexOf(this));
            });
        });
    });
}

// 响应式导航
function initializeResponsiveNav() {
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const navLinks = document.querySelector('.nav-links');
            navLinks.classList.toggle('show');
        });
    }
}

// 表单验证函数
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// 显示通知消息
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 在现有代码后添加
function validatePasswordForm() {
    const form = document.getElementById('password-form');
    const newPassword = document.getElementById('new_password');
    const confirmPassword = document.getElementById('confirm_password');
    
    form.addEventListener('submit', function(e) {
        if (newPassword.value !== confirmPassword.value) {
            e.preventDefault();
            showNotification('新密码和确认密码不匹配！', 'error');
            confirmPassword.classList.add('is-invalid');
        }
    });
} 