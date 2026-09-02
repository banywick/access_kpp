<!-- frontend/src/components/contractor/ContractorDashboard.vue -->
<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="user-greeting">
        <span class="greeting-icon">👋</span>
        <div>
          <h2>Здравствуйте, {{ userData.full_name }}!</h2>
          <p class="user-phone">{{ userData.phone_number }}</p>
        </div>
      </div>
      
      <button class="logout-btn" @click="onLogout">
        <span>🚪</span>
        <span>Выйти</span>
      </button>
    </div>
    
    <div class="dashboard-status">
      <div class="status-card" :class="{ verified: userData.is_verified, pending: !userData.is_verified }">
        <span class="status-icon">{{ userData.is_verified ? '✅' : '⏳' }}</span>
        <div>
          <p class="status-title">Статус верификации</p>
          <p class="status-text">{{ userData.is_verified ? 'Верифицирован' : 'Ожидает верификации' }}</p>
        </div>
      </div>
    </div>
    
    <!-- QR Код и Access Code -->
    <div v-if="qrData && userData.is_verified" class="access-section">
      <h3>Ваши данные для прохода</h3>
      
      <div class="access-container">
        <!-- QR Код -->
        <div class="qr-wrapper">
          <img 
            v-if="qrData.qr_image" 
            :src="qrData.qr_image" 
            alt="QR Code"
            class="qr-image"
          />
          <div v-else class="qr-placeholder">
            <div class="spinner"></div>
            <p>Генерация QR-кода...</p>
          </div>
        </div>
        
        <!-- Access Code -->
        <div class="code-wrapper">
          <div class="code-display">
            <span class="code-label">🔑 Код доступа</span>
            <span class="code-value">{{ accessCode || '----' }}</span>
          </div>
          <p class="code-hint">
            Покажите QR-код или назовите код охраннику
          </p>
        </div>
      </div>
      
      <div class="action-buttons">
        <button class="action-btn download-btn" @click="downloadQR">
          <span>⬇️</span>
          <span>Скачать QR</span>
        </button>
        <button class="action-btn copy-btn" @click="copyQRCode">
          <span>📋</span>
          <span>Скопировать QR</span>
        </button>
        <button class="action-btn code-btn" @click="copyAccessCode">
          <span>🔑</span>
          <span>Скопировать код</span>
        </button>
      </div>
    </div>
    
    <!-- Информация о пользователе -->
    <div class="user-info">
      <h3>Информация</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Телефон</span>
          <span class="info-value">{{ userData.phone_number }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">ФИО</span>
          <span class="info-value">{{ userData.full_name }}</span>
        </div>
        <div class="info-item" v-if="userData.patronymic">
          <span class="info-label">Отчество</span>
          <span class="info-value">{{ userData.patronymic }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Код доступа</span>
          <span class="info-value code-highlight">{{ accessCode || 'Не сгенерирован' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Статус</span>
          <span class="info-value" :class="userData.is_verified ? 'verified' : 'pending'">
            {{ userData.is_verified ? '✅ Верифицирован' : '⏳ Ожидает' }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Если не верифицирован -->
    <div v-if="!userData.is_verified" class="verification-prompt">
      <div class="prompt-icon">📸</div>
      <h3>Требуется верификация</h3>
      <p>Загрузите фото для верификации личности</p>
      <button class="verify-btn" @click="goToPhotoUpload">
        Загрузить фото
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContractorDashboard',
  props: {
    userData: {
      type: Object,
      required: true
    },
    qrData: {
      type: Object,
      default: null
    }
  },
  computed: {
    accessCode() {
      return this.userData.access_code || this.qrData?.access_code || null
    }
  },
  methods: {
    goToPhotoUpload() {
      this.$emit('go-to-photo')
    },
    
    onLogout() {
      if (confirm('Вы уверены, что хотите выйти?')) {
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('userRole')
        localStorage.removeItem('userData')
        this.$emit('logout')
      }
    },
    
    downloadQR() {
      if (!this.qrData || !this.qrData.qr_image) return
      
      const link = document.createElement('a')
      link.download = `qr_${this.userData.phone_number}.png`
      link.href = this.qrData.qr_image
      link.click()
    },
    
    async copyQRCode() {
      try {
        if (this.qrData.qr_image) {
          const response = await fetch(this.qrData.qr_image)
          const blob = await response.blob()
          
          await navigator.clipboard.write([
            new ClipboardItem({
              [blob.type]: blob
            })
          ])
          
          this.showNotification('✅ QR-код скопирован в буфер обмена')
        }
      } catch (error) {
        console.error('Ошибка копирования:', error)
        if (this.qrData.qr_code) {
          await navigator.clipboard.writeText(this.qrData.qr_code)
          this.showNotification('✅ QR-код скопирован как текст')
        }
      }
    },
    
    async copyAccessCode() {
      if (!this.accessCode) {
        this.showNotification('❌ Код доступа не сгенерирован', 'error')
        return
      }
      
      try {
        await navigator.clipboard.writeText(this.accessCode)
        this.showNotification('✅ Код доступа скопирован: ' + this.accessCode)
      } catch (error) {
        console.error('Ошибка копирования:', error)
        this.showNotification('❌ Не удалось скопировать код', 'error')
      }
    },
    
    showNotification(message, type = 'success') {
      const notification = document.createElement('div')
      notification.className = `notification ${type}`
      notification.textContent = message
      document.body.appendChild(notification)
      
      setTimeout(() => {
        notification.classList.add('show')
      }, 100)
      
      setTimeout(() => {
        notification.classList.remove('show')
        setTimeout(() => {
          document.body.removeChild(notification)
        }, 300)
      }, 3000)
    }
  }
}
</script>

<style scoped>
.dashboard {
  animation: fadeIn 0.3s ease;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 15px;
}

.greeting-icon {
  font-size: 40px;
}

.user-greeting h2 {
  font-size: 22px;
  color: #1a237e;
  margin: 0;
}

.user-phone {
  color: #666;
  font-size: 14px;
  margin: 5px 0 0 0;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  color: #666;
}

.logout-btn:hover {
  background: #fce4ec;
  color: #c62828;
}

.dashboard-status {
  margin-bottom: 25px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  border-radius: 12px;
  background: #f5f5f5;
}

.status-card.verified {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
}

.status-card.pending {
  background: #fff3e0;
  border: 1px solid #ffcc80;
}

.status-icon {
  font-size: 28px;
}

.status-title {
  font-weight: 600;
  color: #333;
  margin: 0;
}

.status-text {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}

/* Access Section */
.access-section {
  text-align: center;
  padding: 20px 0;
  border-top: 2px solid #f0f0f0;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 20px;
}

.access-section h3 {
  color: #1a237e;
  margin-bottom: 20px;
}

.access-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.qr-wrapper {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 250px;
}

.qr-image {
  width: 100%;
  height: auto;
  display: block;
}

.qr-placeholder {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #f5f5f5;
  border-radius: 8px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #1a237e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.code-wrapper {
  width: 100%;
  max-width: 300px;
}

.code-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 15px 20px;
  background: #f8f9ff;
  border: 2px dashed #1a237e;
  border-radius: 12px;
}

.code-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.code-value {
  font-size: 36px;
  font-weight: 700;
  color: #1a237e;
  font-family: 'Courier New', monospace;
  letter-spacing: 4px;
}

.code-hint {
  font-size: 13px;
  color: #999;
  margin: 5px 0 0 0;
}

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 15px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.action-btn:active {
  transform: scale(0.95);
}

.download-btn {
  background: #1a237e;
  color: white;
}

.download-btn:hover {
  background: #0d47a1;
}

.copy-btn {
  background: #f5f5f5;
  color: #333;
}

.copy-btn:hover {
  background: #e0e0e0;
}

.code-btn {
  background: #e8f5e9;
  color: #2e7d32;
}

.code-btn:hover {
  background: #c8e6c9;
}

/* User Info */
.user-info {
  margin-top: 10px;
}

.user-info h3 {
  color: #333;
  font-size: 16px;
  margin-bottom: 10px;
}

.info-grid {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #666;
  font-weight: 500;
  font-size: 14px;
}

.info-value {
  color: #1a237e;
  font-weight: 600;
  font-size: 14px;
}

.info-value.verified {
  color: #2e7d32;
}

.info-value.pending {
  color: #e65100;
}

.code-highlight {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  color: #1a237e;
  background: #e8eaf6;
  padding: 0 10px;
  border-radius: 4px;
}

/* Verification Prompt */
.verification-prompt {
  text-align: center;
  padding: 30px 20px;
  background: #fff3e0;
  border-radius: 12px;
  margin-top: 20px;
  border: 2px dashed #ffcc80;
}

.prompt-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.verification-prompt h3 {
  color: #e65100;
  margin-bottom: 5px;
}

.verification-prompt p {
  color: #666;
  margin-bottom: 15px;
}

.verify-btn {
  padding: 12px 30px;
  background: linear-gradient(135deg, #ff6f00 0%, #e65100 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.verify-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(230, 81, 0, 0.3);
}

.notification {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: #1a237e;
  color: white;
  padding: 14px 24px;
  border-radius: 10px;
  font-size: 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  opacity: 0;
  transition: all 0.3s ease;
  z-index: 9999;
  max-width: 90%;
}

.notification.show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

.notification.error {
  background: #c62828;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .dashboard-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .user-greeting h2 {
    font-size: 18px;
  }
  
  .greeting-icon {
    font-size: 32px;
  }
  
  .qr-wrapper {
    max-width: 200px;
    padding: 15px;
  }
  
  .code-value {
    font-size: 28px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    width: 100%;
    max-width: 200px;
    justify-content: center;
  }
  
  .info-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>