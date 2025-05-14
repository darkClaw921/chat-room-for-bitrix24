/**
 * Основные JavaScript функции для приложения
 */

// Функция для проверки авторизации
function checkAuth() {
    const token = localStorage.getItem('token');
    const publicPaths = ['/login', '/'];
    
    // Если нет токена и страница не публичная, перенаправляем на страницу входа
    if (!token && !publicPaths.includes(window.location.pathname)) {
        window.location.href = '/login';
        return false;
    }
    
    // Если есть токен и мы на странице входа, перенаправляем на страницу чатов
    if (token && window.location.pathname === '/login') {
        window.location.href = '/chats';
        return false;
    }
    
    return true;
}

// Функция для выполнения API запросов с авторизацией
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        window.location.href = '/login';
        return null;
    }
    
    // Добавляем заголовок авторизации
    const headers = {
        'Authorization': `Bearer ${token}`,
        ...(options.headers || {})
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Токен недействителен
            localStorage.removeItem('token');
            window.location.href = '/login';
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`Ошибка запроса: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API ошибка:', error);
        return null;
    }
}

// Функция для форматирования даты
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date >= today) {
        // Сегодня - показываем только время
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (date >= yesterday) {
        // Вчера
        return 'Вчера';
    } else {
        // Другие дни - показываем дату
        return date.toLocaleDateString();
    }
}

// Проверяем авторизацию при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    
    // Обработчик выхода из системы
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('token');
            window.location.href = '/login';
        });
    }
    
    // Обработчик переключения темы
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const theme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Обновляем иконку
            const themeIcon = document.getElementById('theme-icon');
            if (themeIcon) {
                if (newTheme === 'dark') {
                    themeIcon.classList.replace('bi-sun', 'bi-moon');
                } else {
                    themeIcon.classList.replace('bi-moon', 'bi-sun');
                }
            }
        });
    }
}); 