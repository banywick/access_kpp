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
              @keyup.enter="checkManualCode"
              :disabled="isLoading"
              ref="codeInput"
            />
            <button 
              @click="checkManualCode" 
              class="scan-btn primary" 
              :disabled="isLoading || !isCodeValid"
            >
              <span v-if="isLoading" class="spinner"></span>
              <span v-else>🔍 Проверить</span>
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
        
        <!-- Результат -->
        <div v-if="scanResult" class="scan-result" :class="scanResult.success ? 'success' : 'error'">
          <div class="result-header">
            <div class="result-icon-wrapper">
              <span class="result-icon">{{ scanResult.success ? '✅' : '❌' }}</span>
            </div>
            <div class="result-title">
              <h3>{{ scanResult.success ? 'Доступ разрешен!' : 'Доступ запрещен!' }}</h3>
              <p class="result-message">{{ scanResult.message }}</p>
            </div>
          </div>
          
          <div v-if="scanResult.contractor" class="contractor-info">
            <div class="contractor-photo-wrapper" @click="openPhotoModal">
              <div class="contractor-photo">
                <img 
                  v-if="scanResult.contractor.photo" 
                  :src="'http://localhost:8000' + scanResult.contractor.photo" 
                  :alt="scanResult.contractor.full_name"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <div v-if="!scanResult.contractor.photo" class="no-photo">👤</div>
              </div>
              <div class="photo-expand-hint">
                <span>🔍</span>
                <span>Нажмите для увеличения</span>
              </div>
            </div>
            
            <div class="contractor-details">
              <div class="detail-item">
                <span class="detail-label">ФИО</span>
                <span class="detail-value">{{ scanResult.contractor.full_name || 'Не указано' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Телефон</span>
                <span class="detail-value">{{ scanResult.contractor.phone_number || 'Не указан' }}</span>
              </div>
              <div class="detail-item" v-if="scanResult.contractor.patronymic">
                <span class="detail-label">Отчество</span>
                <span class="detail-value">{{ scanResult.contractor.patronymic }}</span>
              </div>
              <div class="detail-item" v-if="scanResult.contractor.is_verified !== undefined">
                <span class="detail-label">Статус</span>
                <span class="detail-value" :class="scanResult.contractor.is_verified ? 'verified' : 'unverified'">
                  {{ scanResult.contractor.is_verified ? '✅ Верифицирован' : '❌ Не верифицирован' }}
                </span>
              </div>
              <div class="detail-item" v-if="scanResult.access_method">
                <span class="detail-label">Способ входа</span>
                <span class="detail-value">{{ scanResult.access_method === 'qr' ? '📷 QR-код' : '🔑 Код доступа' }}</span>
              </div>
              <div class="detail-item" v-if="scanResult.reason">
                <span class="detail-label">Причина</span>
                <span class="detail-value error-text">{{ scanResult.reason }}</span>
              </div>
              <div class="detail-item" v-if="scanResult.access_time">
                <span class="detail-label">Время прохода</span>
                <span class="detail-value">{{ formatTime(scanResult.access_time) }}</span>
              </div>
            </div>
          </div>
          
          <div v-else class="no-contractor">
            <p>👤 Информация о пользователе не найдена</p>
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
          :src="'http://localhost:8000' + scanResult?.contractor?.photo" 
          :alt="scanResult?.contractor?.full_name"
          class="modal-photo"
          @error="(e) => e.target.style.display = 'none'"
        />
        <div class="modal-photo-info">
          <p class="modal-photo-name">{{ scanResult?.contractor?.full_name }}</p>
          <p class="modal-photo-phone">{{ scanResult?.contractor?.phone_number }}</p>
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
      isCameraActive: false,
      scanResult: null,
      stream: null,
      scanInterval: null,
      showPhotoModal: false
    }
  },
  computed: {
    isCodeValid() {
      return this.manualCode.length === 4 && /^\d{4}$/.test(this.manualCode)
    }
  },
  methods: {
    formatCodeInput() {
      this.manualCode = this.manualCode.replace(/\D/g, '').slice(0, 4)
    },
    
    async checkManualCode() {
      if (!this.isCodeValid) {
        this.scanResult = {
          success: false,
          message: 'Введите 4 цифры кода доступа'
        }
        return
      }
      
      this.isLoading = true
      this.scanResult = null
      
      try {
        const response = await axios.post('/api/scan-qr/', {
          access_code: this.manualCode
        })
        
        this.scanResult = {
          success: true,
          message: response.data.message || 'Проезд разрешен ✅',
          contractor: response.data.contractor,
          access_time: response.data.access_time,
          access_method: 'code'
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        this.scanResult = {
          success: false,
          message: errorData.message || 'Доступ запрещен ❌',
          reason: errorData.reason || errorData.error,
          contractor: errorData.contractor,
          access_method: 'code'
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async startCamera() {
      try {
        this.scanResult = null
        this.manualCode = ''
        
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
        
        const response = await axios.post('/api/scan-qr/', {
          qr_code: qrData
        })
        
        this.scanResult = {
          success: true,
          message: response.data.message || 'Проезд разрешен ✅',
          contractor: response.data.contractor,
          access_time: response.data.access_time,
          access_method: 'qr'
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        this.scanResult = {
          success: false,
          message: errorData.message || 'Доступ запрещен ❌',
          reason: errorData.reason || errorData.error,
          contractor: errorData.contractor,
          access_method: 'qr'
        }
      }
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
      this.scanResult = null
      this.manualCode = ''
      this.isLoading = false
      this.showPhotoModal = false
      this.$refs.codeInput?.focus()
    },
    
    openPhotoModal() {
      if (this.scanResult?.contractor?.photo) {
        this.showPhotoModal = true
        document.body.style.overflow = 'hidden'
      }
    },
    
    closePhotoModal() {
      this.showPhotoModal = false
      document.body.style.overflow = ''
    },
    
    formatTime(timeString) {
      if (!timeString) return ''
      try {
        const date = new Date(timeString)
        return date.toLocaleTimeString('ru-RU', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
      } catch {
        return timeString
      }
    }
  },
  beforeUnmount() {
    this.stopCamera()
    document.body.style.overflow = ''
  }
}
</script>

<style scoped>
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
  margin-bottom: 30px;
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
  min-width: 140px;
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

.scan-result {
  margin-top: 10px;
  padding: 24px;
  border-radius: 16px;
  animation: fadeIn 0.4s ease;
}

.scan-result.success {
  background: #e8f5e9;
  border: 2px solid #4CAF50;
}

.scan-result.error {
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

.contractor-info {
  display: flex;
  gap: 20px;
  margin: 15px 0 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  backdrop-filter: blur(10px);
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

.detail-value.error-text {
  color: #c62828;
}

.detail-value.verified {
  color: #2e7d32;
}

.detail-value.unverified {
  color: #e65100;
}

.no-contractor {
  text-align: center;
  padding: 15px;
  color: #888;
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