/**
 * Основные JavaScript функции для приложения
 */

// Функция для получения куки по имени
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Функция для проверки авторизации
function checkAuth() {
    const token = getCookie('token') || localStorage.getItem('token');
    const publicPaths = ['/login', '/'];
    
    // Проверка для страниц, требующих авторизации
    if (!token && !publicPaths.includes(window.location.pathname)) {
        // Не используем перенаправление JS, это будет сделано на сервере
        // window.location.href = '/login';
        return false;
    }
    
    // Если пользователь авторизован и находится на странице логина
    if (token && window.location.pathname === '/login') {
        window.location.href = '/chats';
        return false;
    }
    
    return true;
}

// Функция выхода из системы
async function logout() {
    try {
        // Вызываем API для выхода (очистка куки на сервере)
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        // Очищаем localStorage
        localStorage.removeItem('token');
        
        // Перенаправляем на страницу входа
        window.location.href = '/login';
    } catch (error) {
        console.error('Ошибка при выходе:', error);
        // Перенаправляем на страницу входа даже при ошибке
        window.location.href = '/login';
    }
}

// Функция для обновления токена
async function refreshToken() {
    const token = getCookie('token') || localStorage.getItem('token');
    
    // Если нет токена, не пытаемся обновить
    if (!token) {
        return false;
    }
    
    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            credentials: 'include' // Важно для работы с куками
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Ошибка обновления токена:', error);
        return false;
    }
}

// Функция для выполнения API запросов с авторизацией
async function apiRequest(url, options = {}) {
    const token = getCookie('token') || localStorage.getItem('token');
    
    if (!token) {
        window.location.href = '/login';
        return null;
    }
    
    // Добавляем заголовок авторизации и поддержку кук
    const headers = {
        'Authorization': `Bearer ${token}`,
        ...(options.headers || {})
    };
    
    const requestOptions = {
        ...options,
        headers,
        credentials: 'include' // Важно для работы с куками
    };
    
    try {
        const response = await fetch(url, requestOptions);
        
        if (response.status === 401) {
            // Токен недействителен, пробуем обновить
            const refreshed = await refreshToken();
            if (refreshed) {
                // Повторяем запрос с новым токеном
                return apiRequest(url, options);
            } else {
                // Если не удалось обновить токен, перенаправляем на страницу входа
                localStorage.removeItem('token');
                window.location.href = '/login';
                return null;
            }
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
    // Вызываем проверку авторизации
    checkAuth();
    
    // Обработчик выхода из системы
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
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
    
    // Если пользователь авторизован, запускаем периодическое обновление токена
    const token = getCookie('token') || localStorage.getItem('token');
    if (token) {
        // Проверяем и обновляем токен каждые 30 минут
        setInterval(refreshToken, 30 * 60 * 1000);
        
        // И также сразу пробуем обновить токен при загрузке
        refreshToken();
    }
});