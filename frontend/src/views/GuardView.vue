<!-- frontend/src/views/GuardView.vue -->
<template>
  <div class="guard-view">
    <div class="guard-container">
      <div class="header-section">
        <h1>🛡️ Проверка доступа</h1>
        <p class="subtitle">Сканируйте QR-код или введите код доступа вручную</p>
      </div>
      
      <div class="scanner-section">
        <!-- Ручной ввод кода -->
        <div class="manual-input">
          <label for="codeInput">Введите код доступа (4 цифры):</label>
          <div class="code-input-wrapper">
            <input
              id="codeInput"
              v-model="manualCode"
              type="text"
              maxlength="4"
              placeholder="• • • •"
              class="code-input"
              @input="formatCodeInput"
              @keyup.enter="findContractor"
              :disabled="isLoading"
              ref="codeInput"
            />
            <button 
              @click="findContractor" 
              class="scan-btn primary" 
              :disabled="isLoading || !isCodeValid"
            >
              <span v-if="isLoading" class="spinner"></span>
              <span v-else>🔍 Найти</span>
            </button>
          </div>
        </div>
        
        <div class="divider">
          <span>или</span>
        </div>
        
        <button 
          @click="startCamera" 
          class="scan-btn camera-btn" 
          v-if="!isCameraActive && !isLoading"
        >
          <span>📷</span>
          <span>Сканировать QR-код</span>
        </button>
        
        <div v-if="isCameraActive" class="camera-container">
          <video 
            ref="video" 
            class="camera-video" 
            autoplay 
            playsinline
          ></video>
          <div class="camera-overlay">
            <div class="scan-frame"></div>
            <div class="scan-line"></div>
          </div>
          <button @click="stopCamera" class="scan-btn danger camera-stop-btn">
            <span>⏹️</span>
            <span>Остановить</span>
          </button>
          <p class="camera-hint">Наведите камеру на QR-код</p>
        </div>
        
        <!-- Карточка подрядчика -->
        <div v-if="contractorFound" class="contractor-card">
          <div class="card-header">
            <span class="card-icon">👤</span>
            <h3>Информация о подрядчике</h3>
          </div>
          
          <div class="contractor-info">
            <div class="contractor-photo-wrapper" @click="openPhotoModal">
              <div class="contractor-photo">
                <img 
                  v-if="contractorData?.photo" 
                  :src="'http://localhost:8000' + contractorData.photo" 
                  :alt="contractorData.full_name"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <div v-if="!contractorData?.photo" class="no-photo">👤</div>
              </div>
              <div class="photo-expand-hint">
                <span>🔍</span>
                <span>Увеличить</span>
              </div>
            </div>
            
            <div class="contractor-details">
              <div class="detail-item">
                <span class="detail-label">ФИО</span>
                <span class="detail-value">{{ contractorData?.full_name || 'Не указано' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Телефон</span>
                <span class="detail-value">{{ contractorData?.phone_number || 'Не указан' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Организация</span>
                <span class="detail-value">{{ contractorData?.organization || 'Не указана' }}</span>
              </div>
              <div class="detail-item" v-if="contractorData?.patronymic">
                <span class="detail-label">Отчество</span>
                <span class="detail-value">{{ contractorData.patronymic }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Статус</span>
                <span class="detail-value" :class="isOnTerritory ? 'verified' : 'unverified'">
                  {{ isOnTerritory ? '📍 На территории' : '🚫 Не на территории' }}
                </span>
              </div>
              <div class="detail-item" v-if="daysRemaining !== null">
                <span class="detail-label">Дней доступа</span>
                <span class="detail-value" :class="getDaysClass(daysRemaining)">
                  {{ daysRemaining }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Кнопки действий -->
          <div class="action-buttons">
            <button 
              class="action-btn entry-btn" 
              @click="processAccess('entry')"
              :disabled="isProcessing || isOnTerritory"
            >
              🚗 Заехал
            </button>
            <button 
              class="action-btn exit-btn" 
              @click="processAccess('exit')"
              :disabled="isProcessing || !isOnTerritory"
            >
              🚗 Выехал
            </button>
          </div>
          
          <div v-if="actionResult" class="action-result" :class="actionResult.success ? 'success' : 'error'">
            <span class="result-icon">{{ actionResult.success ? '✅' : '❌' }}</span>
            <span>{{ actionResult.message }}</span>
          </div>
          
          <button @click="resetScanner" class="scan-btn primary reset-btn">
            <span>🔄</span>
            <span>Новый поиск</span>
          </button>
        </div>
        
        <!-- Результат ошибки -->
        <div v-if="scanError" class="scan-result error">
          <div class="result-header">
            <div class="result-icon-wrapper">
              <span class="result-icon">❌</span>
            </div>
            <div class="result-title">
              <h3>Доступ запрещен!</h3>
              <p class="result-message">{{ scanErrorMessage }}</p>
            </div>
          </div>
          <button @click="resetScanner" class="scan-btn primary reset-btn">
            <span>🔄</span>
            <span>Проверить снова</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для увеличения фото -->
    <div v-if="showPhotoModal" class="photo-modal" @click="closePhotoModal">
      <div class="photo-modal-content" @click.stop>
        <button class="modal-close-btn" @click="closePhotoModal">✕</button>
        <img 
          :src="'http://localhost:8000' + contractorData?.photo" 
          :alt="contractorData?.full_name"
          class="modal-photo"
          @error="(e) => e.target.style.display = 'none'"
        />
        <div class="modal-photo-info">
          <p class="modal-photo-name">{{ contractorData?.full_name }}</p>
          <p class="modal-photo-phone">{{ contractorData?.phone_number }}</p>
          <p class="modal-photo-org">🏢 {{ contractorData?.organization || 'Не указана' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import jsQR from 'jsqr'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
axios.defaults.withCredentials = true

export default {
  name: 'GuardView',
  data() {
    return {
      manualCode: '',
      isLoading: false,
      isProcessing: false,
      isCameraActive: false,
      contractorFound: false,
      contractorData: null,
      isOnTerritory: false,
      daysRemaining: null,
      scanError: false,
      scanErrorMessage: '',
      actionResult: null,
      stream: null,
      scanInterval: null,
      showPhotoModal: false,
      currentUser: null // Данные текущего пользователя (охранника)
    }
  },
  computed: {
    isCodeValid() {
      return this.manualCode.length === 4 && /^\d{4}$/.test(this.manualCode)
    }
  },
  mounted() {
    // Загружаем данные текущего пользователя из localStorage
    const userDataStr = localStorage.getItem('userData')
    if (userDataStr) {
      try {
        this.currentUser = JSON.parse(userDataStr)
        console.log('Current user (guard):', this.currentUser)
      } catch (e) {
        console.error('Ошибка парсинга userData:', e)
      }
    }
  },
  methods: {
    getCsrfToken() {
      const name = 'csrftoken'
      let cookieValue = null
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
            break
          }
        }
      }
      return cookieValue
    },
    
    getDaysClass(days) {
      if (days === 'Истек' || days === 'Заблокирован' || days === '—') return 'expired'
      if (typeof days !== 'number') return ''
      if (days <= 3) return 'danger'
      if (days <= 7) return 'warning'
      return 'success'
    },
    
    formatCodeInput() {
      this.manualCode = this.manualCode.replace(/\D/g, '').slice(0, 4)
    },
    
    calculateDaysRemaining(validUntil) {
      if (!validUntil) return '—'
      
      const today = new Date()
      const until = new Date(validUntil)
      const diffTime = until - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays < 0) return '⏰ Истек'
      return diffDays
    },
    
    async findContractor() {
      if (!this.isCodeValid) {
        this.showError('Введите 4 цифры кода доступа')
        return
      }
      
      this.isLoading = true
      this.resetState()
      
      try {
        const csrfToken = this.getCsrfToken()
        const response = await axios.post('/api/get-contractor-info/', {
          access_code: this.manualCode
        }, {
          headers: { 'X-CSRFToken': csrfToken }
        })
        
        console.log('Find contractor response:', response.data)
        
        if (response.data.success) {
          this.contractorFound = true
          this.contractorData = response.data.contractor
          this.isOnTerritory = response.data.is_on_territory || false
          this.daysRemaining = this.calculateDaysRemaining(response.data.valid_until)
          this.scanError = false
          this.actionResult = null
        }
      } catch (error) {
        console.error('Find contractor error:', error.response?.data)
        const errorData = error.response?.data || {}
        this.showError(errorData.message || errorData.reason || 'Подрядчик не найден')
        this.contractorData = errorData.contractor || null
        if (this.contractorData) {
          this.contractorFound = true
          this.isOnTerritory = errorData.is_on_territory || false
          this.daysRemaining = this.calculateDaysRemaining(errorData.valid_until)
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async startCamera() {
      try {
        this.resetState()
        
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            facingMode: 'environment',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }
        })
        
        this.$refs.video.srcObject = this.stream
        await this.$refs.video.play()
        this.isCameraActive = true
        
        this.scanInterval = setInterval(this.scanFrame, 500)
      } catch (error) {
        console.error('Ошибка доступа к камере:', error)
        alert('Не удалось открыть камеру. Используйте ручной ввод кода.')
      }
    },
    
    scanFrame() {
      if (!this.$refs.video) return
      
      const canvas = document.createElement('canvas')
      const video = this.$refs.video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      })
      
      if (code && code.data) {
        this.processQRCode(code.data)
      }
    },
    
    async processQRCode(qrData) {
      try {
        this.stopCamera()
        this.isLoading = true
        this.resetState()
        
        const csrfToken = this.getCsrfToken()
        const response = await axios.post('/api/get-contractor-info/', {
          qr_code: qrData
        }, {
          headers: { 'X-CSRFToken': csrfToken }
        })
        
        console.log('QR Find response:', response.data)
        
        if (response.data.success) {
          this.contractorFound = true
          this.contractorData = response.data.contractor
          this.isOnTerritory = response.data.is_on_territory || false
          this.daysRemaining = this.calculateDaysRemaining(response.data.valid_until)
          this.scanError = false
          this.actionResult = null
        }
      } catch (error) {
        console.error('QR Find error:', error.response?.data)
        const errorData = error.response?.data || {}
        this.showError(errorData.message || errorData.reason || 'Подрядчик не найден')
        this.contractorData = errorData.contractor || null
        if (this.contractorData) {
          this.contractorFound = true
          this.isOnTerritory = errorData.is_on_territory || false
          this.daysRemaining = this.calculateDaysRemaining(errorData.valid_until)
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async processAccess(type) {
    this.isProcessing = true
    this.actionResult = null
    
    try {
        const csrfToken = this.getCsrfToken()
        
        // Собираем данные для отправки
        const requestData = {
            access_code: this.contractorData?.access_code,
            access_type: type,
            guard_id: this.currentUser?.id,  // Используем ID вместо телефона
            guard_phone: this.currentUser?.phone_number,
            guard_name: this.currentUser?.full_name
        }
        
        console.log('Process access request:', requestData)
        
        const response = await axios.post('/api/scan-qr/', requestData, {
            headers: { 'X-CSRFToken': csrfToken }
        })
        
        console.log('Process access response:', response.data)
        
        if (response.data.success) {
            this.isOnTerritory = response.data.is_on_territory || false
            if (response.data.contractor) {
                this.contractorData = response.data.contractor
            }
            if (response.data.valid_until) {
                this.daysRemaining = this.calculateDaysRemaining(response.data.valid_until)
            }
            this.actionResult = {
                success: true,
                message: response.data.message || 'Операция выполнена успешно'
            }
        }
    } catch (error) {
        console.error('Process access error:', error.response?.data)
        const errorData = error.response?.data || {}
        this.actionResult = {
            success: false,
            message: errorData.message || errorData.reason || 'Ошибка операции'
        }
    } finally {
        this.isProcessing = false
    }
},
    
    showError(message) {
      this.scanError = true
      this.scanErrorMessage = message
      this.contractorFound = false
    },
    
    resetState() {
      this.contractorFound = false
      this.contractorData = null
      this.isOnTerritory = false
      this.daysRemaining = null
      this.scanError = false
      this.scanErrorMessage = ''
      this.actionResult = null
    },
    
    stopCamera() {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop())
        this.stream = null
      }
      if (this.scanInterval) {
        clearInterval(this.scanInterval)
        this.scanInterval = null
      }
      this.isCameraActive = false
    },
    
    resetScanner() {
      this.resetState()
      this.manualCode = ''
      this.isLoading = false
      this.isProcessing = false
      this.showPhotoModal = false
      this.stopCamera()
      this.$refs.codeInput?.focus()
    },
    
    openPhotoModal() {
      if (this.contractorData?.photo) {
        this.showPhotoModal = true
        document.body.style.overflow = 'hidden'
      }
    },
    
    closePhotoModal() {
      this.showPhotoModal = false
      document.body.style.overflow = ''
    }
  },
  beforeUnmount() {
    this.stopCamera()
    document.body.style.overflow = ''
  }
}
</script>

<style scoped>
/* Все стили остаются без изменений */
.guard-view {
  min-height: 80vh;
  padding: 20px;
  background: #f0f2f5;
}

.guard-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08);
}

.header-section {
  text-align: center;
  margin-bottom: 25px;
}

.header-section h1 {
  font-size: 28px;
  color: #1a237e;
  margin-bottom: 5px;
}

.subtitle {
  color: #888;
  font-size: 15px;
}

.scanner-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.manual-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.manual-input label {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}

.code-input-wrapper {
  display: flex;
  gap: 12px;
}

.code-input {
  flex: 1;
  padding: 16px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 28px;
  font-family: 'Courier New', monospace;
  text-align: center;
  letter-spacing: 12px;
  transition: border-color 0.3s, box-shadow 0.3s;
  background: #fafafa;
}

.code-input:focus {
  outline: none;
  border-color: #1a237e;
  box-shadow: 0 0 0 4px rgba(26, 35, 126, 0.1);
  background: white;
}

.code-input:disabled {
  opacity: 0.6;
  background: #f5f5f5;
}

.code-input::placeholder {
  color: #ccc;
  font-size: 20px;
  letter-spacing: 4px;
}

.scan-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  justify-content: center;
  flex-shrink: 0;
}

.scan-btn:active {
  transform: scale(0.97);
}

.scan-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.scan-btn.primary {
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  color: white;
  min-width: 120px;
}

.scan-btn.primary:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
}

.scan-btn.camera-btn {
  background: linear-gradient(135deg, #00695c 0%, #004d40 100%);
  color: white;
  width: 100%;
  padding: 18px;
  font-size: 18px;
}

.scan-btn.camera-btn:hover {
  box-shadow: 0 4px 15px rgba(0, 105, 92, 0.3);
}

.scan-btn.danger {
  background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%);
  color: white;
}

.scan-btn.danger:hover {
  box-shadow: 0 4px 15px rgba(198, 40, 40, 0.3);
}

.divider {
  text-align: center;
  color: #bbb;
  margin: 5px 0;
  position: relative;
}

.divider span {
  background: white;
  padding: 0 15px;
  position: relative;
  z-index: 1;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e0e0e0;
}

.camera-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.scan-frame {
  width: 65%;
  height: 65%;
  border: 3px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.3);
}

.scan-line {
  position: absolute;
  top: 17.5%;
  left: 17.5%;
  right: 17.5%;
  height: 3px;
  background: #4CAF50;
  box-shadow: 0 0 20px #4CAF50, 0 0 60px rgba(76, 175, 80, 0.3);
  animation: scanLine 2s ease-in-out infinite;
}

@keyframes scanLine {
  0% { top: 17.5%; }
  50% { top: 77.5%; }
  100% { top: 17.5%; }
}

.camera-stop-btn {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  width: auto;
}

.camera-hint {
  position: absolute;
  top: 20px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
  pointer-events: none;
  letter-spacing: 0.5px;
}

.spinner {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.contractor-card {
  border: 2px solid #1a237e;
  border-radius: 16px;
  padding: 20px;
  animation: fadeIn 0.4s ease;
  background: #f8f9ff;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.card-icon {
  font-size: 24px;
}

.card-header h3 {
  font-size: 18px;
  color: #1a237e;
  margin: 0;
}

.contractor-info {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.contractor-photo-wrapper {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.contractor-photo-wrapper:hover {
  transform: scale(1.02);
}

.contractor-photo {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  transition: border-color 0.3s, box-shadow 0.3s;
}

.contractor-photo-wrapper:hover .contractor-photo {
  border-color: #1a237e;
  box-shadow: 0 4px 20px rgba(26, 35, 126, 0.3);
}

.contractor-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-photo {
  font-size: 36px;
}

.photo-expand-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #888;
  opacity: 0;
  transition: opacity 0.3s;
}

.contractor-photo-wrapper:hover .photo-expand-hint {
  opacity: 1;
}

.contractor-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #888;
  font-weight: 500;
  font-size: 13px;
}

.detail-value {
  font-weight: 600;
  color: #1a237e;
  text-align: right;
  font-size: 13px;
}

.detail-value.verified {
  color: #2e7d32;
}

.detail-value.unverified {
  color: #e65100;
}

.detail-value.success {
  color: #2e7d32;
}

.detail-value.warning {
  color: #e65100;
}

.detail-value.danger {
  color: #c62828;
}

.detail-value.expired {
  color: #999;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin: 15px 0;
}

.action-btn {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:active {
  transform: scale(0.96);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.entry-btn {
  background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
  color: white;
}

.entry-btn:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);
}

.exit-btn {
  background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%);
  color: white;
}

.exit-btn:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(198, 40, 40, 0.3);
}

.action-result {
  padding: 12px 16px;
  border-radius: 10px;
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.action-result.success {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}

.action-result.error {
  background: #fce4ec;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.result-icon {
  font-size: 20px;
}

.reset-btn {
  width: 100%;
  margin-top: 5px;
  background: #f5f5f5;
  color: #333;
}

.reset-btn:hover {
  background: #e0e0e0;
}

.scan-result.error {
  padding: 24px;
  border-radius: 16px;
  background: #fce4ec;
  border: 2px solid #e53935;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.result-icon-wrapper {
  flex-shrink: 0;
}

.result-icon {
  font-size: 40px;
}

.result-title h3 {
  font-size: 22px;
  margin: 0;
  color: #333;
}

.result-message {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 15px;
}

.photo-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.photo-modal-content {
  position: relative;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 22px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.modal-close-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: rotate(90deg);
}

.modal-photo {
  width: 100%;
  height: auto;
  max-height: 70vh;
  object-fit: contain;
  display: block;
  background: #f5f5f5;
}

.modal-photo-info {
  padding: 20px;
  text-align: center;
  background: white;
}

.modal-photo-name {
  font-size: 22px;
  font-weight: 700;
  color: #1a237e;
  margin: 0 0 5px 0;
}

.modal-photo-phone {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.modal-photo-org {
  font-size: 16px;
  color: #333;
  margin: 5px 0 0 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@media (max-width: 768px) {
  .guard-container {
    padding: 20px;
  }
  
  .header-section h1 {
    font-size: 24px;
  }
  
  .code-input {
    font-size: 24px;
    padding: 14px 16px;
    letter-spacing: 8px;
  }
  
  .scan-btn.primary {
    min-width: 100px;
    padding: 14px 18px;
    font-size: 14px;
  }
  
  .contractor-photo {
    width: 80px;
    height: 80px;
  }
  
  .photo-modal-content {
    max-width: 95%;
  }
}

@media (max-width: 480px) {
  .guard-view {
    padding: 10px;
  }
  
  .guard-container {
    padding: 16px;
    border-radius: 16px;
  }
  
  .header-section h1 {
    font-size: 20px;
  }
  
  .subtitle {
    font-size: 13px;
  }
  
  .code-input-wrapper {
    flex-direction: column;
  }
  
  .code-input {
    font-size: 22px;
    padding: 14px;
    letter-spacing: 6px;
  }
  
  .scan-btn.primary {
    width: 100%;
    min-width: auto;
  }
  
  .contractor-info {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .contractor-photo-wrapper {
    margin-bottom: 5px;
  }
  
  .contractor-photo {
    width: 120px;
    height: 120px;
  }
  
  .photo-expand-hint {
    opacity: 1;
    font-size: 10px;
  }
  
  .detail-item {
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }
  
  .detail-value {
    text-align: center;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .result-header {
    flex-direction: column;
    text-align: center;
  }
  
  .result-title h3 {
    font-size: 20px;
  }
  
  .modal-photo-name {
    font-size: 18px;
  }
  
  .modal-photo-phone {
    font-size: 14px;
  }
}
</style>