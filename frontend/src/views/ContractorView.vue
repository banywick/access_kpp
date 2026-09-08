<!-- frontend/src/views/ContractorView.vue -->
<template>
  <div class="contractor-view">
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
          
          <div v-if="uploadSuccess" class="success-message">
            ✅ {{ uploadSuccess }}
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
              <div v-else-if="qrImage" class="qr-display">
                <div class="qr-image-wrapper">
                  <img 
                    :src="qrImage" 
                    alt="QR Code"
                    class="qr-image"
                  />
                </div>
                <div class="access-code">
                  <span class="code-label">Код доступа:</span>
                  <span class="code-value">{{ accessCode || '----' }}</span>
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
                <span class="info-label">Статус доступа</span>
                <span class="info-value" :class="getAccessStatusClass(isAllowed)">
                  {{ getAccessStatusText(isAllowed) }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Организация</span>
                <span class="info-value">{{ user.organization || 'Не указана' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Телефон</span>
                <span class="info-value">{{ user.phone || user.phone_number || 'Не указан' }}</span>
              </div>
              <div class="info-item" v-if="user.full_name">
                <span class="info-label">ФИО</span>
                <span class="info-value">{{ user.full_name }}</span>
              </div>
              <div class="info-item" v-if="validUntil">
                <span class="info-label">Действителен до</span>
                <span class="info-value">{{ formatDate(validUntil) }}</span>
              </div>
              <div class="info-item" v-if="daysRemaining !== null">
                <span class="info-label">Дней доступа</span>
                <span class="info-value" :class="getDaysClass(daysRemaining)">
                  {{ formatDaysRemaining(daysRemaining) }}
                </span>
              </div>
              <!-- Причина запрета - отдельное поле -->
              <div class="info-item" v-if="banReason">
                <span class="info-label">Комментарий</span>
                <span class="info-value error-text">{{ banReason }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import api from '../config/axios'

export default {
  name: 'ContractorView',
  data() {
    return {
      user: {
        id: null,
        full_name: '',
        first_name: '',
        last_name: '',
        phone: '',
        phone_number: '',
        is_verified: false,
        organization: '',
        role: 'contractor',
        photo: null,
        access_code: null,
        qr_code: null
      },
      previewImage: null,
      selectedFile: null,
      uploading: false,
      uploadError: null,
      uploadSuccess: null,
      qrCode: null,
      qrImage: null,
      accessCode: null,
      qrLoading: false,
      qrError: null,
      copied: false,
      daysRemaining: null,
      validUntil: null,
      isAllowed: false,
      accessStatus: 'запрещен',
      banReason: null
    }
  },
  mounted() {
    this.loadUserData()
  },
  methods: {
    loadUserData() {
      const userData = localStorage.getItem('userData')
      if (userData) {
        try {
          const parsed = JSON.parse(userData)
          this.user = {
            ...this.user,
            ...parsed,
            phone: parsed.phone || parsed.phone_number || '',
            phone_number: parsed.phone || parsed.phone_number || ''
          }
          console.log('User data loaded:', this.user)
        } catch (e) {
          console.error('Error parsing user data:', e)
        }
      }
      
      if (this.user.is_verified) {
        this.loadQRCode()
      }
    },
    
    async loadQRCode() {
      this.qrLoading = true
      this.qrError = null
      
      try {
        const response = await api.get('/get-qr/')
        console.log('QR Response:', response.data)
        
        if (response.data.success) {
          this.qrCode = response.data.qr_code
          this.qrImage = response.data.qr_image
          this.accessCode = response.data.access_code
          
          // Получаем информацию о доступе из ответа
          this.daysRemaining = response.data.days_remaining
          this.validUntil = response.data.valid_until
          this.isAllowed = response.data.is_allowed
          this.accessStatus = response.data.access_status
          this.banReason = response.data.ban_reason
          
          // Обновляем данные пользователя
          this.user = {
            ...this.user,
            full_name: response.data.full_name || this.user.full_name,
            phone: response.data.phone || this.user.phone,
            phone_number: response.data.phone || this.user.phone_number,
            organization: response.data.organization || this.user.organization,
            photo: response.data.photo || this.user.photo,
            is_verified: true
          }
          
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
        } else if (error.response?.status === 403) {
          this.qrError = 'Пользователь еще не верифицирован.'
        } else {
          this.qrError = error.response?.data?.message || 'Ошибка загрузки QR кода'
        }
      } finally {
        this.qrLoading = false
      }
    },
    
    getAccessStatusText(isAllowed) {
      if (isAllowed) {
        return '✅ Разрешен'
      }
      return '❌ Запрещен'
    },
    
    getAccessStatusClass(isAllowed) {
      if (isAllowed) return 'success'
      return 'error'
    },
    
    formatDaysRemaining(days) {
      if (days === null || days === undefined) return '—'
      if (days === 0) return '⏰ Истек'
      if (days < 0) return '⏰ Истек'
      return days
    },
    
    getDaysClass(days) {
      if (days === null || days === undefined) return 'expired'
      if (days === 0 || days < 0) return 'expired'
      if (days <= 3) return 'danger'
      if (days <= 7) return 'warning'
      return 'success'
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        })
      } catch {
        return dateString
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
      this.uploadSuccess = null
      
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
      this.uploadSuccess = null
      
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
          this.user.is_verified = true
          this.user.photo = response.data.photo_url
          this.accessCode = response.data.access_code
          this.qrCode = response.data.qr_code
          
          const currentData = JSON.parse(localStorage.getItem('userData') || '{}')
          const updatedData = {
            ...currentData,
            ...this.user,
            is_verified: true,
            photo: response.data.photo_url || currentData.photo,
            access_code: response.data.access_code,
            qr_code: response.data.qr_code
          }
          localStorage.setItem('userData', JSON.stringify(updatedData))
          
          this.uploadSuccess = 'Фото загружено! Вы верифицированы.'
          this.previewImage = null
          this.selectedFile = null
          
          setTimeout(() => {
            this.loadQRCode()
          }, 500)
          
        } else {
          this.uploadError = response.data.message || 'Ошибка загрузки фото'
        }
      } catch (error) {
        console.error('Upload error:', error)
        if (error.response?.status === 403) {
          this.uploadError = 'Недостаточно прав. Пожалуйста, войдите заново.'
          setTimeout(() => {
            this.$router.push('/')
          }, 3000)
        } else {
          this.uploadError = error.response?.data?.message || 'Ошибка загрузки фото'
        }
      } finally {
        this.uploading = false
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
  min-height: 100vh;
  background: #f5f7fa;
}

.main-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 30px 20px;
}

.container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #ffc107;
}

.status-card.verified {
  border-left-color: #4caf50;
}

.status-icon {
  font-size: 32px;
}

.status-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #1a237e;
}

.status-text p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.photo-upload-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.photo-upload-card h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #1a237e;
}

.upload-hint {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
}

.upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s, background 0.3s;
  margin-bottom: 16px;
}

.upload-area:hover {
  border-color: #1a237e;
  background: #f8f9ff;
}

.upload-placeholder .upload-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.upload-placeholder p {
  margin: 0 0 4px 0;
  color: #333;
  font-size: 16px;
}

.upload-placeholder small {
  color: #999;
  font-size: 13px;
}

.upload-preview {
  position: relative;
  display: inline-block;
}

.upload-preview img {
  max-height: 200px;
  border-radius: 8px;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  color: white;
  font-weight: 500;
}

.upload-preview:hover .preview-overlay {
  opacity: 1;
}

.upload-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.3s;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  margin-top: 12px;
  padding: 12px;
  background: #fde8e8;
  color: #c62828;
  border-radius: 8px;
  font-size: 14px;
}

.success-message {
  margin-top: 12px;
  padding: 12px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid #a5d6a7;
}

.qr-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.qr-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.qr-card h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #1a237e;
}

.qr-hint {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

.qr-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qr-loading .spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #1a237e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

.qr-loading p {
  color: #666;
  margin: 0;
}

.qr-error {
  text-align: center;
}

.qr-error .error-icon {
  font-size: 40px;
  display: block;
  margin-bottom: 8px;
}

.qr-error p {
  color: #666;
  margin: 0 0 12px 0;
}

.retry-btn {
  padding: 8px 24px;
  background: #1a237e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.qr-image-wrapper {
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: inline-block;
}

.qr-image {
  max-width: 250px;
  max-height: 250px;
  width: 100%;
  height: auto;
  display: block;
}

.access-code {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  background: #f8f9ff;
  padding: 12px 20px;
  border-radius: 8px;
  flex-wrap: wrap;
}

.code-label {
  color: #666;
  font-size: 14px;
}

.code-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a237e;
  font-family: 'Courier New', monospace;
  letter-spacing: 4px;
}

.copy-btn {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

.copy-btn:hover {
  background: #f0f0f0;
}

.code-hint {
  margin: 0;
  color: #999;
  font-size: 13px;
}

.access-info-card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.access-info-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1a237e;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #666;
  font-weight: 500;
}

.info-value {
  color: #1a237e;
  font-weight: 600;
}

.info-value.success {
  color: #2e7d32;
}

.info-value.error {
  color: #c62828;
}

.info-value.warning {
  color: #e65100;
}

.info-value.danger {
  color: #c62828;
}

.info-value.expired {
  color: #999;
}

.error-text {
  color: #c62828;
}

.status-active {
  color: #2e7d32;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .main-content {
    padding: 15px 10px;
  }
  
  .qr-image {
    max-width: 180px;
  }
  
  .access-code {
    flex-wrap: wrap;
  }
  
  .code-value {
    font-size: 20px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>