<!-- frontend/src/views/ContractorView.vue -->
<template>
  <div class="contractor-view">
    <!-- Шапка -->
    <header class="header">
      <div class="header-content">
        <div class="logo-section">
          <span class="logo-icon">🏢</span>
          <h1 class="logo-text">Электронный пропуск</h1>
        </div>
        <div class="user-section">
          <span class="user-name">{{ user.full_name || user.phone }}</span>
          <button @click="logout" class="logout-btn">Выйти</button>
        </div>
      </div>
    </header>

    <!-- Основной контент -->
    <main class="main-content">
      <div class="container">
        <!-- Статус верификации -->
        <div class="status-card" :class="{ verified: user.is_verified }">
          <div class="status-icon">
            {{ user.is_verified ? '✅' : '⏳' }}
          </div>
          <div class="status-text">
            <h3>{{ user.is_verified ? 'Верификация пройдена' : 'Ожидает верификации' }}</h3>
            <p v-if="!user.is_verified">
              Пожалуйста, загрузите свое фото для верификации
            </p>
            <p v-else>
              Ваш аккаунт верифицирован. Используйте QR код для доступа
            </p>
          </div>
        </div>

        <!-- Загрузка фото -->
        <div v-if="!user.is_verified" class="photo-upload-card">
          <h3>📸 Загрузите фото для верификации</h3>
          <p class="upload-hint">Загрузите свое фото для идентификации</p>
          
          <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleFileSelect" 
              accept="image/*"
              style="display: none"
            />
            <div v-if="!previewImage" class="upload-placeholder" @click="$refs.fileInput.click()">
              <span class="upload-icon">📷</span>
              <p>Нажмите или перетащите фото сюда</p>
              <small>Поддерживаются JPG, PNG, WEBP</small>
            </div>
            <div v-else class="upload-preview" @click="$refs.fileInput.click()">
              <img :src="previewImage" alt="Preview" />
              <div class="preview-overlay">
                <span>Изменить фото</span>
              </div>
            </div>
          </div>

          <button 
            @click="uploadPhoto" 
            :disabled="!previewImage || uploading"
            class="upload-btn"
          >
            {{ uploading ? 'Загрузка...' : 'Отправить на верификацию' }}
          </button>
          
          <div v-if="uploadError" class="error-message">
            {{ uploadError }}
          </div>
        </div>

        <!-- QR код и код доступа -->
        <div v-if="user.is_verified" class="qr-section">
          <div class="qr-card">
            <h3>📱 Ваш QR код</h3>
            <p class="qr-hint">Покажите этот QR код охраннику для входа</p>
            
            <div class="qr-container">
              <div v-if="qrLoading" class="qr-loading">
                <div class="spinner"></div>
                <p>Загрузка QR кода...</p>
              </div>
              <div v-else-if="qrError" class="qr-error">
                <span class="error-icon">❌</span>
                <p>{{ qrError }}</p>
                <button @click="loadQRCode" class="retry-btn">Повторить</button>
              </div>
              <div v-else-if="qrCode" class="qr-display">
                <div class="qr-image-wrapper">
                  <img 
                    :src="qrCodeImageUrl" 
                    alt="QR Code"
                    class="qr-image"
                    @error="handleQRError"
                  />
                </div>
                <div class="access-code">
                  <span class="code-label">Код доступа:</span>
                  <span class="code-value">{{ accessCode }}</span>
                  <button @click="copyAccessCode" class="copy-btn">
                    {{ copied ? '✅' : '📋' }}
                  </button>
                </div>
                <p class="code-hint">Используйте этот код для входа через КПП</p>
              </div>
            </div>
          </div>

          <!-- Информация о доступе -->
          <div class="access-info-card">
            <h3>📋 Информация о доступе</h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Статус</span>
                <span class="info-value status-active">
                  ✅ Активен
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Организация</span>
                <span class="info-value">{{ user.organization || 'Не указана' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Телефон</span>
                <span class="info-value">{{ user.phone }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios'

// Создаем экземпляр axios
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Интерцептор для добавления токена
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

// Интерцептор для обработки 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('userData')
      localStorage.removeItem('userRole')
      localStorage.removeItem('isAuthenticated')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default {
  name: 'ContractorView',
  data() {
    return {
      user: {
        full_name: '',
        phone: '',
        is_verified: false,
        organization: '',
        role: 'contractor'
      },
      previewImage: null,
      selectedFile: null,
      uploading: false,
      uploadError: null,
      qrCode: null,
      accessCode: null,
      qrLoading: false,
      qrError: null,
      copied: false
    }
  },
  computed: {
    qrCodeImageUrl() {
      if (!this.qrCode) return ''
      // Используем наш бэкенд для генерации QR кода
      return `http://localhost:8000/api/get-qr/?code=${this.qrCode}`
    }
  },
  mounted() {
    // Загружаем данные пользователя из localStorage
    const userData = localStorage.getItem('userData')
    if (userData) {
      this.user = JSON.parse(userData)
    }
    
    // Загружаем QR код
    if (this.user.is_verified) {
      this.loadQRCode()
    }
  },
  methods: {
    async loadQRCode() {
      this.qrLoading = true
      this.qrError = null
      
      try {
        const response = await api.get('/get-qr/')
        console.log('QR Response:', response.data)
        
        if (response.data.success) {
          this.qrCode = response.data.qr_code
          this.accessCode = response.data.access_code
          
          // Обновляем данные пользователя
          this.user = {
            ...this.user,
            ...response.data
          }
          
          // Сохраняем обновленные данные
          localStorage.setItem('userData', JSON.stringify(this.user))
        } else {
          this.qrError = response.data.message || 'Ошибка загрузки QR кода'
        }
      } catch (error) {
        console.error('Error loading QR:', error)
        
        if (error.response?.status === 401) {
          this.qrError = 'Сессия истекла. Пожалуйста, войдите заново.'
          setTimeout(() => {
            this.$router.push('/')
          }, 3000)
        } else {
          this.qrError = error.response?.data?.message || 'Ошибка загрузки QR кода'
        }
      } finally {
        this.qrLoading = false
      }
    },
    
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.processFile(file)
      }
    },
    
    handleDrop(event) {
      const file = event.dataTransfer.files[0]
      if (file) {
        this.processFile(file)
      }
    },
    
    processFile(file) {
      if (!file.type.startsWith('image/')) {
        this.uploadError = 'Пожалуйста, загрузите изображение'
        return
      }
      
      if (file.size > 5 * 1024 * 1024) {
        this.uploadError = 'Размер файла не должен превышать 5MB'
        return
      }
      
      this.selectedFile = file
      this.uploadError = null
      
      const reader = new FileReader()
      reader.onload = (e) => {
        this.previewImage = e.target.result
      }
      reader.readAsDataURL(file)
    },
    
    async uploadPhoto() {
      if (!this.selectedFile) {
        this.uploadError = 'Выберите файл для загрузки'
        return
      }
      
      this.uploading = true
      this.uploadError = null
      
      const formData = new FormData()
      formData.append('photo', this.selectedFile)
      
      try {
        const response = await api.post('/upload-photo/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        })
        
        console.log('Upload response:', response.data)
        
        if (response.data.success) {
          // Обновляем статус пользователя
          this.user.is_verified = true
          this.user.photo = response.data.photo_url
          
          // Сохраняем в localStorage
          localStorage.setItem('userData', JSON.stringify(this.user))
          
          // Загружаем QR код
          await this.loadQRCode()
          
          this.uploadError = null
          this.previewImage = null
          this.selectedFile = null
          
          // Показываем уведомление об успехе
          alert('✅ Фото успешно загружено! QR код теперь доступен.')
        } else {
          this.uploadError = response.data.message || 'Ошибка загрузки фото'
        }
      } catch (error) {
        console.error('Upload error:', error)
        this.uploadError = error.response?.data?.message || 'Ошибка загрузки фото'
      } finally {
        this.uploading = false
      }
    },
    
    handleQRError(event) {
      console.error('QR image error:', event)
      // Если не загрузился через внешний API, пробуем через наш бэкенд
      if (this.qrCode) {
        // Просто показываем код доступа
        this.qrError = 'Не удалось загрузить QR код, но код доступа доступен ниже'
      }
    },
    
    copyAccessCode() {
      if (!this.accessCode) return
      
      navigator.clipboard.writeText(this.accessCode).then(() => {
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      }).catch(() => {
        // Fallback
        const input = document.createElement('input')
        input.value = this.accessCode
        document.body.appendChild(input)
        input.select()
        document.execCommand('copy')
        document.body.removeChild(input)
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      })
    },
    
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('userData')
      localStorage.removeItem('userRole')
      localStorage.removeItem('isAuthenticated')
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.contractor-view {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.contractor-container {
  width: 100%;
  max-width: 600px;
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 20px;
  border: 4px solid #e0e0e0;
  border-top-color: #1a237e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.redirect-message {
  text-align: center;
  padding: 40px 20px;
}

.redirect-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.redirect-message h2 {
  color: #1a237e;
  margin-bottom: 10px;
}

.redirect-message p {
  color: #666;
  margin-bottom: 20px;
}

.go-home-btn {
  padding: 12px 30px;
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.go-home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .contractor-container {
    padding: 20px;
    border-radius: 12px;
  }
}
</style>