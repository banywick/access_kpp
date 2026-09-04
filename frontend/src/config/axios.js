// frontend/src/config/axios.js

import axios from 'axios'

// Создаем экземпляр axios с базовым URL
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',  // Полный URL
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Добавляем интерцептор для добавления токена
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Интерцептор для обработки ошибок (обновление токена)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // Если токен истек и это не повторный запрос
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('Нет refresh токена')
        }
        
        // Обновляем токен
        const response = await axios.post('/api/token/refresh/', {
          refresh: refreshToken
        })
        
        const { access } = response.data
        localStorage.setItem('access_token', access)
        
        // Повторяем запрос с новым токеном
        originalRequest.headers.Authorization = `Bearer ${access}`
        return api(originalRequest)
      } catch (refreshError) {
        // Не удалось обновить токен - выходим
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api