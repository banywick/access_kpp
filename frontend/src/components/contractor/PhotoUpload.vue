<!-- frontend/src/components/contractor/PhotoUpload.vue -->
<template>
    <div class="photo-upload">
      <div class="step-header">
        <span class="step-number">2</span>
        <h2>Загрузка фото</h2>
      </div>
      
      <div class="user-info-banner">
        <p class="banner-text">
          👋 <strong>{{ userData.full_name }}</strong>, загрузите фото для верификации
        </p>
        <p class="banner-hint">Это необходимо для получения QR-кода доступа</p>
      </div>
      
      <div class="photo-options">
        <button 
          class="option-btn camera-btn" 
          @click="openCamera"
          :disabled="isLoading"
        >
          <span class="option-icon">📷</span>
          <span>Сделать фото</span>
        </button>
        
        <button 
          class="option-btn gallery-btn" 
          @click="selectFile"
          :disabled="isLoading"
        >
          <span class="option-icon">🖼️</span>
          <span>Из галереи</span>
        </button>
      </div>
      
      <div v-if="imagePreview" class="preview-container">
        <img :src="imagePreview" alt="Preview" class="preview-image"/>
        
        <div class="action-buttons">
          <button 
            class="action-btn confirm-btn" 
            @click="confirmPhoto"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="btn-spinner"></span>
            <span v-else>✅ Отправить</span>
          </button>
          
          <button 
            class="action-btn cancel-btn" 
            @click="resetPhoto"
            :disabled="isLoading"
          >
            ❌ Отменить
          </button>
        </div>
      </div>
      
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ Math.round(uploadProgress) }}%</span>
      </div>
      
      <div v-if="statusMessage" class="status-message" :class="statusType">
        {{ statusMessage }}
      </div>
      
      <video 
        v-show="isCameraActive" 
        ref="video" 
        autoplay 
        playsinline
        class="camera-preview"
      ></video>
      
      <!-- Если пользователь уже верифицирован, показываем кнопку пропуска -->
      <div v-if="userData && userData.is_verified" class="skip-section">
        <button class="skip-btn" @click="skipPhoto">
          ⏭️ Пропустить (уже верифицирован)
        </button>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = 'X-CSRFToken'
  axios.defaults.withCredentials = true
  
  export default {
    name: 'PhotoUpload',
    props: {
      phoneNumber: {
        type: String,
        required: true
      },
      userData: {
        type: Object,
        required: true
      }
    },
    data() {
      return {
        imagePreview: null,
        selectedFile: null,
        isCameraActive: false,
        isLoading: false,
        uploadProgress: 0,
        statusMessage: null,
        statusType: 'info',
        stream: null
      }
    },
    methods: {
      openCamera() {
        this.statusMessage = null
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          this.showStatus('Камера не поддерживается на этом устройстве', 'error')
          return
        }
        
        navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          } 
        })
        .then(stream => {
          this.stream = stream
          this.isCameraActive = true
          this.$refs.video.srcObject = stream
          this.showStatus('📸 Фото будет сделано автоматически через 3 секунды', 'info')
          
          setTimeout(this.capturePhoto, 3000)
        })
        .catch(error => {
          this.showStatus('Не удалось открыть камеру: ' + error.message, 'error')
        })
      },
      
      capturePhoto() {
        if (!this.$refs.video) return
        
        const canvas = document.createElement('canvas')
        const video = this.$refs.video
        canvas.width = video.videoWidth || 640
        canvas.height = video.videoHeight || 480
        canvas.getContext('2d').drawImage(video, 0, 0)
        
        this.imagePreview = canvas.toDataURL('image/jpeg', 0.9)
        this.isCameraActive = false
        
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop())
          this.stream = null
        }
        
        canvas.toBlob((blob) => {
          this.selectedFile = new File([blob], 'photo.jpg', { type: 'image/jpeg' })
        }, 'image/jpeg', 0.9)
        
        this.showStatus('Фото сделано! Нажмите "Отправить" для подтверждения', 'info')
      },
      
      selectFile() {
        this.statusMessage = null
        
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = 'image/*'
        
        input.onchange = (e) => {
          const file = e.target.files[0]
          if (file) {
            if (file.size > 5 * 1024 * 1024) {
              this.showStatus('Файл слишком большой. Максимальный размер 5MB', 'error')
              return
            }
            
            this.selectedFile = file
            const reader = new FileReader()
            reader.onload = (event) => {
              this.imagePreview = event.target.result
              this.showStatus('Фото загружено! Нажмите "Отправить" для подтверждения', 'info')
            }
            reader.readAsDataURL(file)
          }
        }
        
        input.click()
      },
      
      async confirmPhoto() {
        if (!this.imagePreview || !this.selectedFile) {
          this.showStatus('Фото не выбрано', 'error')
          return
        }
        
        this.isLoading = true
        this.uploadProgress = 0
        this.statusMessage = null
        
        try {
          const formData = new FormData()
          formData.append('phone_number', this.phoneNumber)
          formData.append('photo', this.selectedFile)
          
          this.uploadProgress = 30
          
          const response = await axios.post('/api/upload-photo/', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const percentCompleted = (progressEvent.loaded * 100) / progressEvent.total
                this.uploadProgress = 30 + (percentCompleted * 0.4)
              }
            }
          })
          
          this.uploadProgress = 70
          
          if (response.data.success) {
            // Проверяем фото на наличие лица
            const verifyResponse = await axios.post('/api/verify-photo/', {
              phone_number: this.phoneNumber
            })
            
            this.uploadProgress = 100
            
            if (verifyResponse.data.success) {
              this.showStatus('✅ Регистрация успешно завершена!', 'success')
              
              setTimeout(() => {
                this.$emit('verified', verifyResponse.data)
              }, 1500)
            } else {
              this.showStatus(verifyResponse.data.error || '❌ Ошибка проверки фото', 'error')
              this.uploadProgress = 0
            }
          } else {
            this.showStatus(response.data.error || '❌ Ошибка загрузки', 'error')
            this.uploadProgress = 0
          }
        } catch (error) {
          console.error('Upload error:', error)
          let errorMsg = 'Ошибка загрузки'
          if (error.response?.data?.error) {
            errorMsg = error.response.data.error
          } else if (error.response?.data?.errors) {
            const errors = error.response.data.errors
            errorMsg = Object.values(errors).flat().join(', ')
          } else if (error.message) {
            errorMsg = error.message
          }
          
          this.showStatus('❌ ' + errorMsg, 'error')
          this.uploadProgress = 0
        } finally {
          this.isLoading = false
        }
      },
      
      skipPhoto() {
        this.$emit('skip')
      },
      
      resetPhoto() {
        this.imagePreview = null
        this.selectedFile = null
        this.uploadProgress = 0
        this.statusMessage = null
        this.statusType = 'info'
        
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop())
          this.stream = null
        }
        this.isCameraActive = false
      },
      
      showStatus(message, type) {
        this.statusMessage = message
        this.statusType = type
      }
    },
    beforeUnmount() {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop())
        this.stream = null
      }
    }
  }
  </script>
  
  <style scoped>
  .photo-upload {
    animation: fadeIn 0.3s ease;
  }
  
  .step-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
  }
  
  .step-number {
    background: #1a237e;
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
  
  .user-info-banner {
    background: #e3f2fd;
    border-radius: 10px;
    padding: 15px 20px;
    margin-bottom: 20px;
    border-left: 4px solid #1a237e;
  }
  
  .banner-text {
    font-size: 16px;
    color: #0d47a1;
    margin: 0;
  }
  
  .banner-hint {
    font-size: 14px;
    color: #666;
    margin: 5px 0 0 0;
  }
  
  .photo-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 20px 0;
  }
  
  .option-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 20px;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }
  
  .option-btn:active {
    transform: scale(0.96);
  }
  
  .option-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .option-icon {
    font-size: 36px;
  }
  
  .camera-btn:hover {
    border-color: #1a237e;
    background: #f0f2ff;
  }
  
  .gallery-btn:hover {
    border-color: #0d47a1;
    background: #f0f7ff;
  }
  
  .preview-container {
    margin: 20px 0;
  }
  
  .preview-image {
    width: 100%;
    max-height: 400px;
    object-fit: contain;
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    background: #f5f5f5;
  }
  
  .action-buttons {
    display: flex;
    gap: 12px;
    margin-top: 15px;
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
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  
  .action-btn:active {
    transform: scale(0.96);
  }
  
  .confirm-btn {
    background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%);
    color: white;
  }
  
  .confirm-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .cancel-btn {
    background: #f5f5f5;
    color: #666;
  }
  
  .progress-container {
    margin: 15px 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .progress-bar {
    flex: 1;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #1a237e, #0d47a1);
    border-radius: 3px;
    transition: width 0.3s;
  }
  
  .progress-text {
    font-size: 14px;
    color: #666;
    min-width: 40px;
    text-align: right;
  }
  
  .camera-preview {
    width: 100%;
    max-height: 400px;
    border-radius: 12px;
    background: #000;
    margin-top: 15px;
  }
  
  .status-message {
    margin-top: 15px;
    padding: 14px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    animation: fadeIn 0.3s ease;
  }
  
  .status-message.success {
    background: #e8f5e9;
    color: #1b5e20;
    border: 1px solid #a5d6a7;
  }
  
  .status-message.error {
    background: #fce4ec;
    color: #b71c1c;
    border: 1px solid #ef9a9a;
  }
  
  .status-message.info {
    background: #e3f2fd;
    color: #0d47a1;
    border: 1px solid #90caf9;
  }
  
  .skip-section {
    margin-top: 15px;
    text-align: center;
  }
  
  .skip-btn {
    padding: 10px 20px;
    background: transparent;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    color: #666;
    transition: all 0.3s;
  }
  
  .skip-btn:hover {
    border-color: #1a237e;
    color: #1a237e;
    background: #f8f9ff;
  }
  
  .btn-spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @media (max-width: 480px) {
    .photo-options {
      grid-template-columns: 1fr;
    }
    
    .option-btn {
      flex-direction: row;
      padding: 14px;
      justify-content: center;
    }
    
    .option-icon {
      font-size: 28px;
    }
    
    .action-buttons {
      flex-direction: column;
    }
    
    .preview-image {
      max-height: 300px;
    }
    
    .camera-preview {
      max-height: 300px;
    }
    
    .step-header h2 {
      font-size: 20px;
    }
    
    .step-number {
      width: 34px;
      height: 34px;
      font-size: 16px;
    }
  }
  </style>