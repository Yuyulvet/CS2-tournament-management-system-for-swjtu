// login.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // 阻止默认的表单提交行为

        // 获取表单数据
        const formData = new FormData(form);

        // 提交表单数据
        fetch('/login', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // 处理成功响应
            console.log(data);
            // 显示成功消息或重定向
            alert('Login successful!');
            window.location.href = '/dashboard'; // 重定向到仪表盘或其他页面
        })
        .catch(error => {
            // 处理错误
            console.error('There was a problem with the fetch operation:', error);
            // 显示错误消息
            showAlert('Login failed. Please check your credentials and try again.');
        });
    });

    function showAlert(message) {
        const modal = document.getElementById('alertModal');
        document.getElementById('alertMessage').innerText = message;
        modal.style.display = 'block';
        // 添加一个事件监听器，当用户点击关闭按钮时隐藏弹窗
        modal.querySelector('button').addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
});



