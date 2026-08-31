<!-- frontend/src/components/contractor/QRCodeDisplay.vue -->
<template>
    <div class="qr-display">
      <div class="step-header">
        <span class="step-number">✅</span>
        <h2>Регистрация завершена!</h2>
      </div>
      
      <div class="success-icon">🎉</div>
      
      <p class="user-greeting">
        Здравствуйте, <strong>{{ userData.full_name }}</strong>
      </p>
      
      <div class="qr-container">
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
        
        <div class="qr-info">
          <p class="qr-label">Ваш персональный QR-код</p>
          <p class="qr-hint">
            Покажите этот код охраннику на проходной
          </p>
        </div>
      </div>
      
      <div class="user-info">
        <div class="info-item">
          <span class="info-label">Телефон</span>
          <span class="info-value">{{ userData.phone_number }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">ФИО</span>
          <span class="info-value">{{ userData.full_name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Статус</span>
          <span class="info-value status-verified">✅ Верифицирован</span>
        </div>
      </div>
      
      <div class="button-group">
        <button class="copy-btn" @click="copyQRCode">
          <span>📋</span>
          <span>Скопировать QR-код</span>
        </button>
        
        <button class="reset-btn" @click="resetRegistration">
          🔄 Выйти
        </button>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'QRCodeDisplay',
    props: {
      qrData: {
        type: Object,
        required: true
      },
      userData: {
        type: Object,
        required: true
      }
    },
    methods: {
      async copyQRCode() {
        try {
          if (this.qrData.qr_image) {
            // Конвертируем base64 в blob
            const response = await fetch(this.qrData.qr_image)
            const blob = await response.blob()
            
            await navigator.clipboard.write([
              new ClipboardItem({
                [blob.type]: blob
              })
            ])
            
            this.showNotification('✅ QR-код скопирован в буфер обмена')
          } else if (this.qrData.qr_code) {
            await navigator.clipboard.writeText(this.qrData.qr_code)
            this.showNotification('✅ QR-код скопирован как текст')
          }
        } catch (error) {
          console.error('Ошибка копирования:', error)
          this.showNotification('❌ Не удалось скопировать QR-код', 'error')
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
      },
      
      resetRegistration() {
        this.$emit('reset')
        window.location.reload()
      }
    }
  }
  </script>
  
  <style scoped>
  .qr-display {
    animation: fadeIn 0.3s ease;
    text-align: center;
  }
  
  .step-header {
    display: flex;
    align-items: center;
    gap: 15px;
    justify-content: center;
    margin-bottom: 15px;
  }
  
  .step-number {
    background: #2e7d32;
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
  }
  
  .step-header h2 {
    font-size: 24px;
    color: #1a237e;
    margin: 0;
  }
  
  .success-icon {
    font-size: 64px;
    margin: 10px 0;
  }
  
  .user-greeting {
    font-size: 18px;
    color: #333;
    margin-bottom: 20px;
  }
  
  .qr-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    margin: 20px 0;
  }
  
  .qr-wrapper {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 280px;
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
    background: #f5f5f5;
    border-radius: 8px;
    gap: 10px;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e0e0e0;
    border-top-color: #1a237e;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  .qr-placeholder p {
    color: #666;
    font-size: 14px;
  }
  
  .qr-label {
    font-weight: 600;
    font-size: 18px;
    color: #1a237e;
  }
  
  .qr-hint {
    font-size: 14px;
    color: #666;
    margin-top: 5px;
  }
  
  .user-info {
    background: #f5f7fa;
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
    text-align: left;
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
  }
  
  .info-value {
    color: #1a237e;
    font-weight: 600;
  }
  
  .status-verified {
    color: #2e7d32;
  }
  
  .button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 10px;
  }
  
  .copy-btn, .reset-btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  
  .copy-btn {
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
  }
  
  .copy-btn:active {
    transform: scale(0.98);
  }
  
  .reset-btn {
    background: #f5f5f5;
    color: #666;
  }
  
  .reset-btn:active {
    transform: scale(0.98);
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
    .step-header h2 {
      font-size: 20px;
    }
    
    .step-number {
      width: 34px;
      height: 34px;
      font-size: 16px;
    }
    
    .success-icon {
      font-size: 48px;
    }
    
    .user-greeting {
      font-size: 16px;
    }
    
    .qr-wrapper {
      max-width: 220px;
      padding: 15px;
    }
    
    .info-item {
      font-size: 14px;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
    
    .copy-btn, .reset-btn {
      font-size: 14px;
      padding: 12px;
    }
  }
  </style>