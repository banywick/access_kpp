<!-- frontend/src/views/ContractorView.vue -->
<template>
  <div class="contractor-view">
    <div class="contractor-container">
      <!-- Шаг 1: Ввод телефона (редирект на Welcome) -->
      <div v-if="step === 'phone'" class="redirect-message">
        <div class="redirect-icon">🔄</div>
        <h2>Перенаправление...</h2>
        <p>Пожалуйста, используйте главную страницу для входа</p>
        <button class="go-home-btn" @click="goHome">На главную</button>
      </div>
      
      <!-- Шаг 2: Загрузка фото (только для подрядчиков) -->
      <PhotoUpload
        v-else-if="step === 'photo'"
        :phone-number="phoneNumber"
        :user-data="userData"
        @verified="onPhotoVerified"
        @skip="onSkipPhoto"
      />
      
      <!-- Шаг 3: Личный кабинет с QR кодом (только для подрядчиков) -->
      <ContractorDashboard
        v-else-if="step === 'dashboard'"
        :user-data="userData"
        :qr-data="qrData"
        @logout="onLogout"
        @go-to-photo="step = 'photo'"
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
import PhotoUpload from '../components/contractor/PhotoUpload.vue'
import ContractorDashboard from '../components/contractor/ContractorDashboard.vue'
import axios from 'axios'

export default {
  name: 'ContractorView',
  components: {
    PhotoUpload,
    ContractorDashboard
  },
  data() {
    return {
      step: 'loading',
      phoneNumber: null,
      userData: null,
      qrData: null
    }
  },
  mounted() {
    // Проверяем авторизацию
    const isAuth = localStorage.getItem('isAuthenticated')
    const userRole = localStorage.getItem('userRole')
    const userDataStr = localStorage.getItem('userData')
    
    if (isAuth === 'true' && userDataStr) {
      try {
        this.userData = JSON.parse(userDataStr)
        this.phoneNumber = this.userData.phone_number
        
        // Проверяем роль - если охранник или админ, редирект на админку
        if (userRole === 'guard' || userRole === 'admin') {
          this.$router.push('/admin')
          return
        }
        
        // Только для подрядчиков
        // Если верифицирован - показываем дашборд
        if (this.userData.is_verified && this.userData.qr_code) {
          this.step = 'dashboard'
          this.loadQRCode()
        } else {
          this.step = 'photo'
        }
      } catch (e) {
        this.goHome()
      }
    } else {
      this.goHome()
    }
  },
  methods: {
    goHome() {
      this.$router.push('/')
    },
    
    onPhotoVerified(data) {
      console.log('Photo verified:', data)
      this.qrData = data
      this.userData = data.contractor || this.userData
      
      // Обновляем данные в localStorage
      if (this.userData) {
        localStorage.setItem('userData', JSON.stringify(this.userData))
      }
      
      this.step = 'dashboard'
    },
    
    onSkipPhoto() {
      if (this.userData && this.userData.is_verified) {
        this.loadQRCode()
        this.step = 'dashboard'
      } else {
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
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('userRole')
      localStorage.removeItem('userData')
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