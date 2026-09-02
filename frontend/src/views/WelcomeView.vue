<!-- frontend/src/views/WelcomeView.vue -->
<template>
    <div class="welcome-view">
      <div class="welcome-container">
        <!-- Логотип и заголовок -->
        <div class="welcome-header">
          <div class="logo-container">
            <div class="logo-icon">🏢</div>
            <h1 class="company-name">Электронный пропуск</h1>
          </div>
          <p class="company-subtitle">Система контроля доступа предприятия</p>
        </div>
  
        <!-- Основной контент -->
        <div class="welcome-content">
          <div class="illustration">
            <div class="illustration-icon">🔐</div>
            <p class="illustration-text">Безопасный и удобный доступ</p>
          </div>
  
          <div class="auth-section">
            <h2>Вход в систему</h2>
            <p class="auth-hint">Введите номер телефона для входа</p>
  
            <form @submit.prevent="submitPhone" class="auth-form">
              <div class="phone-input-wrapper">
                <span class="country-code">+375</span>
                <input
                  v-model="phoneDisplay"
                  type="tel"
                  placeholder="29 123-45-67"
                  class="phone-input"
                  @input="formatPhoneInput"
                  :disabled="isLoading"
                  maxlength="14"
                  required
                  autofocus
                />
              </div>
  
              <div v-if="phoneError" class="field-error">
                <span class="error-icon">⚠️</span>
                {{ phoneError }}
              </div>
  
              <!-- Поле для пароля (показывается только когда нужно) -->
              <div v-if="showPasswordField" class="password-input-wrapper">
                <input
                  v-model="password"
                  type="password"
                  placeholder="Введите пароль"
                  class="password-input"
                  :disabled="isLoading"
                  required
                />
              </div>
  
              <!-- Согласие на обработку данных -->
              <div class="consent-checkbox">
                <label class="checkbox-label">
                  <input 
                    type="checkbox" 
                    v-model="consentGiven"
                    :disabled="isLoading"
                  />
                  <span class="checkbox-custom"></span>
                  <span class="checkbox-text">
                    Я соглашаюсь на обработку моих персональных данных в соответствии с 
                    <a href="#" @click.prevent="showPrivacyPolicy = true" class="privacy-link">
                      политикой конфиденциальности
                    </a>
                  </span>
                </label>
              </div>
  
              <button 
                type="submit" 
                class="submit-btn"
                :disabled="!isPhoneValid || !consentGiven || isLoading || (showPasswordField && !password)"
              >
                <span v-if="isLoading" class="btn-spinner"></span>
                <span v-else>Войти</span>
              </button>
            </form>
  
            <div v-if="error" class="error-message">
              <span class="error-icon">⚠️</span>
              {{ error }}
            </div>
          </div>
  
          <div class="info-links">
            <p class="help-text">
              💡 Если у вас возникли проблемы, обратитесь к администратору
            </p>
          </div>
        </div>
      </div>
  
      <!-- Модальное окно с политикой конфиденциальности -->
      <div v-if="showPrivacyPolicy" class="modal-overlay" @click.self="showPrivacyPolicy = false">
        <div class="modal privacy-modal">
          <div class="modal-header">
            <h2>🔒 Политика конфиденциальности</h2>
            <button class="close-btn" @click="showPrivacyPolicy = false">✕</button>
          </div>
          <div class="modal-body">
            <h3>1. Общие положения</h3>
            <p>Настоящая политика обработки персональных данных составлена в соответствии с требованиями законодательства.</p>
            
            <h3>2. Какие данные собираются</h3>
            <p>Для работы системы мы собираем следующие данные:</p>
            <ul>
              <li>Номер телефона</li>
              <li>ФИО</li>
              <li>Фотография</li>
              <li>Дата и время прохода</li>
            </ul>
            
            <h3>3. Цели обработки данных</h3>
            <ul>
              <li>Идентификация личности</li>
              <li>Контроль доступа на территорию предприятия</li>
              <li>Ведение журнала проходов</li>
            </ul>
            
            <h3>4. Защита данных</h3>
            <p>Все данные хранятся на защищенных серверах и не передаются третьим лицам.</p>
            
            <h3>5. Согласие</h3>
            <p>Нажимая кнопку "Войти", вы даете согласие на обработку ваших персональных данных.</p>
          </div>
          <div class="modal-footer">
            <button class="agree-btn" @click="acceptPrivacy">Я согласен</button>
          </div>
        </div>
      </div>
  
      <!-- Footer -->
      <div class="welcome-footer">
        <p>© 2024 Система электронных пропусков</p>
        <p class="footer-version">v2.0.0</p>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = 'X-CSRFToken'
  axios.defaults.withCredentials = true
  
  export default {
    name: 'WelcomeView',
    data() {
      return {
        phoneDisplay: '',
        phoneRaw: '',
        password: '',
        isLoading: false,
        error: null,
        phoneError: null,
        consentGiven: false,
        showPrivacyPolicy: false,
        showPasswordField: false
      }
    },
    computed: {
      fullPhoneNumber() {
        const cleaned = this.phoneRaw.replace(/\D/g, '')
        if (cleaned.length === 0) return ''
        const operator = cleaned.slice(0, 2)
        const rest = cleaned.slice(2)
        return '+375' + operator + rest
      },
      isPhoneValid() {
        if (!this.phoneRaw) return false
        const cleaned = this.phoneRaw.replace(/\D/g, '')
        return cleaned.length === 9
      }
    },
    methods: {
      formatPhoneInput() {
        let cleaned = this.phoneDisplay.replace(/\D/g, '')
        
        if (cleaned.length > 9) {
          cleaned = cleaned.slice(0, 9)
        }
        
        this.phoneRaw = cleaned
        
        let formatted = cleaned
        if (cleaned.length > 0) {
          if (cleaned.length >= 2) {
            formatted = cleaned.slice(0, 2)
            if (cleaned.length >= 3) {
              formatted += ' ' + cleaned.slice(2)
            }
            if (cleaned.length >= 6) {
              formatted = formatted.slice(0, 6) + '-' + formatted.slice(6)
            }
            if (cleaned.length >= 8) {
              formatted = formatted.slice(0, 9) + '-' + formatted.slice(9)
            }
          }
        }
        
        this.phoneDisplay = formatted
        this.validatePhone()
      },
      
      validatePhone() {
        const cleaned = this.phoneRaw.replace(/\D/g, '')
        
        if (cleaned.length === 0) {
          this.phoneError = null
          return
        }
        
        if (cleaned.length < 2) {
          this.phoneError = 'Введите код оператора (29, 33, 44, 25)'
          return
        }
        
        const operatorCode = cleaned.slice(0, 2)
        const validCodes = ['29', '33', '44', '25']
        
        if (!validCodes.includes(operatorCode)) {
          this.phoneError = 'Неверный код оператора. Допустимые: 29, 33, 44, 25'
          return
        }
        
        if (cleaned.length < 9) {
          this.phoneError = `Введите еще ${9 - cleaned.length} цифр`
          return
        }
        
        if (cleaned.length === 9) {
          this.phoneError = null
        } else if (cleaned.length > 9) {
          this.phoneError = 'Слишком много цифр'
        }
      },
      
      async submitPhone() {
        if (!this.isPhoneValid) {
          this.error = 'Пожалуйста, введите корректный номер телефона'
          return
        }
        
        if (!this.consentGiven) {
          this.error = 'Необходимо согласие на обработку персональных данных'
          return
        }
        
        if (this.showPasswordField && !this.password) {
          this.error = 'Введите пароль'
          return
        }
        
        this.isLoading = true
        this.error = null
        
        const phoneToSend = this.fullPhoneNumber
        
        try {
          const payload = { phone_number: phoneToSend }
          if (this.showPasswordField) {
            payload.password = this.password
          }
          
          const response = await axios.post('/api/login/', payload)
          
          if (response.data.success) {
            localStorage.setItem('userData', JSON.stringify(response.data.user_data))
            localStorage.setItem('userRole', response.data.role)
            localStorage.setItem('isAuthenticated', 'true')
            
            if (response.data.role === 'guard' || response.data.role === 'admin') {
              this.$router.push('/admin')
            } else {
              this.$router.push('/dashboard')
            }
          } else {
            this.error = response.data.error || 'Ошибка входа'
          }
        } catch (error) {
          console.error('Login error:', error)
          
          if (error.response) {
            const errorData = error.response.data
            
            if (errorData.requires_password) {
              this.showPasswordField = true
              this.error = errorData.error || 'Введите пароль'
              this.password = ''
            } else {
              this.error = errorData.error || errorData.reason || 'Ошибка сервера'
            }
          } else {
            this.error = 'Ошибка соединения с сервером'
          }
        } finally {
          this.isLoading = false
        }
      },
      
      acceptPrivacy() {
        this.showPrivacyPolicy = false
        this.consentGiven = true
      }
    },
    watch: {
      phoneRaw() {
        this.validatePhone()
      }
    },
    mounted() {
      const isAuth = localStorage.getItem('isAuthenticated')
      const userRole = localStorage.getItem('userRole')
      
      if (isAuth === 'true') {
        if (userRole === 'guard' || userRole === 'admin') {
          this.$router.push('/admin')
        } else {
          this.$router.push('/dashboard')
        }
      }
      
      setTimeout(() => {
        const input = document.querySelector('.phone-input')
        if (input) input.focus()
      }, 100)
    }
  }
  </script>
  
  <style scoped>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  .welcome-view {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  }
  
  .welcome-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    max-width: 480px;
    margin: 0 auto;
    width: 100%;
  }
  
  .welcome-header {
    text-align: center;
    margin-bottom: 40px;
  }
  
  .logo-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    margin-bottom: 10px;
  }
  
  .logo-icon {
    font-size: 48px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    width: 70px;
    height: 70px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(26, 35, 126, 0.3);
  }
  
  .company-name {
    font-size: 28px;
    font-weight: 700;
    color: #1a237e;
    margin: 0;
  }
  
  .company-subtitle {
    color: #666;
    font-size: 16px;
    margin: 0;
  }
  
  .welcome-content {
    background: white;
    border-radius: 20px;
    padding: 35px 30px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
    width: 100%;
  }
  
  .illustration {
    text-align: center;
    margin-bottom: 30px;
  }
  
  .illustration-icon {
    font-size: 56px;
    display: block;
    margin-bottom: 8px;
  }
  
  .illustration-text {
    color: #666;
    font-size: 15px;
    margin: 0;
  }
  
  .auth-section h2 {
    font-size: 22px;
    color: #1a237e;
    margin: 0 0 5px 0;
    text-align: center;
  }
  
  .auth-hint {
    color: #888;
    font-size: 14px;
    text-align: center;
    margin: 0 0 25px 0;
  }
  
  .auth-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .phone-input-wrapper {
    display: flex;
    align-items: center;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
    background: white;
  }
  
  .phone-input-wrapper:focus-within {
    border-color: #1a237e;
    box-shadow: 0 0 0 4px rgba(26, 35, 126, 0.1);
  }
  
  .country-code {
    padding: 14px 14px 14px 18px;
    background: #f5f7fa;
    font-weight: 600;
    color: #1a237e;
    font-size: 18px;
    border-right: 1px solid #e0e0e0;
    flex-shrink: 0;
  }
  
  .phone-input {
    flex: 1;
    padding: 14px 16px;
    border: none;
    font-size: 18px;
    outline: none;
    background: transparent;
    min-width: 0;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
  }
  
  .phone-input::placeholder {
    color: #bbb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: normal;
    font-size: 16px;
  }
  
  .phone-input:disabled {
    opacity: 0.7;
    background: #f5f5f5;
  }
  
  .password-input-wrapper {
    display: flex;
    align-items: center;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
    background: white;
  }
  
  .password-input-wrapper:focus-within {
    border-color: #1a237e;
    box-shadow: 0 0 0 4px rgba(26, 35, 126, 0.1);
  }
  
  .password-input {
    flex: 1;
    padding: 14px 16px;
    border: none;
    font-size: 18px;
    outline: none;
    background: transparent;
    min-width: 0;
  }
  
  .password-input::placeholder {
    color: #bbb;
    font-size: 16px;
  }
  
  .password-input:disabled {
    opacity: 0.7;
    background: #f5f5f5;
  }
  
  .field-error {
    color: #c62828;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: -8px;
  }
  
  .error-icon {
    font-size: 16px;
  }
  
  .consent-checkbox {
    margin: 5px 0;
  }
  
  .checkbox-label {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    cursor: pointer;
    font-size: 14px;
    color: #555;
    line-height: 1.4;
  }
  
  .checkbox-label input[type="checkbox"] {
    display: none;
  }
  
  .checkbox-custom {
    min-width: 20px;
    width: 20px;
    height: 20px;
    border: 2px solid #ccc;
    border-radius: 4px;
    position: relative;
    margin-top: 1px;
    transition: all 0.3s;
    flex-shrink: 0;
  }
  
  .checkbox-label input[type="checkbox"]:checked + .checkbox-custom {
    background: #1a237e;
    border-color: #1a237e;
  }
  
  .checkbox-label input[type="checkbox"]:checked + .checkbox-custom::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 14px;
    font-weight: bold;
  }
  
  .checkbox-text {
    user-select: none;
  }
  
  .privacy-link {
    color: #1a237e;
    text-decoration: none;
    font-weight: 600;
  }
  
  .privacy-link:hover {
    text-decoration: underline;
  }
  
  .submit-btn {
    padding: 16px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-top: 5px;
  }
  
  .submit-btn:not(:disabled):active {
    transform: scale(0.98);
  }
  
  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .submit-btn:hover:not(:disabled) {
    box-shadow: 0 4px 20px rgba(26, 35, 126, 0.3);
  }
  
  .btn-spinner {
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
  
  .error-message {
    margin-top: 15px;
    padding: 12px 16px;
    background: #fde8e8;
    border-left: 4px solid #e53935;
    border-radius: 8px;
    color: #c62828;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
  }
  
  .info-links {
    margin-top: 20px;
    text-align: center;
  }
  
  .help-text {
    color: #999;
    font-size: 13px;
    margin: 0;
  }
  
  /* Модальное окно политики */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
    animation: fadeIn 0.3s ease;
  }
  
  .privacy-modal {
    background: white;
    border-radius: 16px;
    max-width: 560px;
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    animation: slideIn 0.3s ease;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e0e0e0;
    flex-shrink: 0;
  }
  
  .modal-header h2 {
    font-size: 20px;
    color: #1a237e;
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
    transition: transform 0.3s;
  }
  
  .close-btn:hover {
    transform: rotate(90deg);
  }
  
  .modal-body {
    padding: 24px;
    overflow-y: auto;
    flex: 1;
  }
  
  .modal-body h3 {
    color: #1a237e;
    font-size: 16px;
    margin: 20px 0 8px 0;
  }
  
  .modal-body h3:first-child {
    margin-top: 0;
  }
  
  .modal-body p {
    color: #555;
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 10px 0;
  }
  
  .modal-body ul {
    color: #555;
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 10px 0;
    padding-left: 20px;
  }
  
  .modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    justify-content: flex-end;
    flex-shrink: 0;
  }
  
  .agree-btn {
    padding: 12px 32px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .agree-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .welcome-footer {
    text-align: center;
    padding: 20px;
    color: #999;
    font-size: 13px;
  }
  
  .welcome-footer p {
    margin: 0;
  }
  
  .footer-version {
    font-size: 11px;
    opacity: 0.6;
    margin-top: 4px !important;
  }
  
  /* Адаптивность */
  @media (max-width: 480px) {
    .welcome-container {
      padding: 20px 15px;
    }
    
    .logo-icon {
      width: 56px;
      height: 56px;
      font-size: 32px;
    }
    
    .company-name {
      font-size: 22px;
    }
    
    .welcome-content {
      padding: 25px 20px;
    }
    
    .phone-input,
    .password-input {
      font-size: 16px;
      padding: 12px 14px;
    }
    
    .country-code {
      padding: 12px 10px 12px 14px;
      font-size: 16px;
    }
    
    .auth-section h2 {
      font-size: 20px;
    }
    
    .submit-btn {
      font-size: 16px;
      padding: 14px;
    }
    
    .privacy-modal {
      max-width: 100%;
      margin: 10px;
    }
    
    .modal-body {
      padding: 16px;
    }
  }
  </style>