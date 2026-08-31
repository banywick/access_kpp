<!-- frontend/src/views/ContractorView.vue -->
<template>
    <div class="contractor-view">
      <div class="contractor-container">
        <!-- Шаг 1: Ввод телефона -->
        <PhoneRegistration 
          v-if="step === 'phone'"
          @verified="onPhoneVerified"
        />
        
        <!-- Шаг 2: Загрузка фото -->
        <PhotoUpload
          v-else-if="step === 'photo'"
          :phone-number="phoneNumber"
          :user-data="userData"
          @verified="onPhotoVerified"
          @skip="onSkipPhoto"
        />
        
        <!-- Шаг 3: Личный кабинет с QR кодом -->
        <ContractorDashboard
          v-else-if="step === 'dashboard'"
          :user-data="userData"
          :qr-data="qrData"
          @logout="onLogout"
        />
        
        <!-- Загрузка -->
        <div v-else class="loading-container">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import PhoneRegistration from '../components/contractor/PhoneRegistration.vue'
  import PhotoUpload from '../components/contractor/PhotoUpload.vue'
  import ContractorDashboard from '../components/contractor/ContractorDashboard.vue'
  import axios from 'axios'
  
  export default {
    name: 'ContractorView',
    components: {
      PhoneRegistration,
      PhotoUpload,
      ContractorDashboard
    },
    data() {
      return {
        step: 'phone',
        phoneNumber: null,
        userData: null,
        qrData: null
      }
    },
    methods: {
      onPhoneVerified(data) {
        console.log('Phone verified:', data)
        this.phoneNumber = data.user_data.phone_number
        this.userData = data.user_data
        
        // Если уже верифицирован и есть QR - сразу в dashboard
        if (data.is_verified && data.has_qr) {
          this.loadQRCode()
          this.step = 'dashboard'
        } else {
          this.step = 'photo'
        }
      },
      
      onPhotoVerified(data) {
        console.log('Photo verified:', data)
        this.qrData = data
        this.userData = data.contractor || this.userData
        this.step = 'dashboard'
      },
      
      onSkipPhoto() {
        // Если пользователь пропустил фото, но уже верифицирован
        if (this.userData && this.userData.is_verified) {
          this.loadQRCode()
          this.step = 'dashboard'
        } else {
          // Если не верифицирован, возвращаем на шаг с фото
          this.step = 'photo'
        }
      },
      
      async loadQRCode() {
        try {
          const response = await axios.post('/api/get-qr/', {
            phone_number: this.phoneNumber
          })
          this.qrData = response.data
        } catch (error) {
          console.error('Ошибка загрузки QR:', error)
        }
      },
      
      onLogout() {
        this.step = 'phone'
        this.phoneNumber = null
        this.userData = null
        this.qrData = null
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