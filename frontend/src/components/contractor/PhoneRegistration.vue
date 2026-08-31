<!-- frontend/src/components/contractor/PhoneRegistration.vue -->
<template>
    <div class="phone-registration">
      <div class="step-header">
        <span class="step-number">1</span>
        <h2>Вход в систему</h2>
      </div>
      
      <p class="step-description">
        Введите номер телефона (Беларусь)<br>
        <span class="hint">Формат: +375 44 458-69-48</span>
      </p>
      
      <form @submit.prevent="submitPhone" class="phone-form">
        <div class="input-group">
          <label for="phone">Номер телефона</label>
          <div class="phone-input-wrapper">
            <span class="country-code">+375</span>
            <input
              id="phone"
              v-model="phoneDisplay"
              type="tel"
              placeholder="44 458-69-48"
              required
              :disabled="isLoading"
              @input="formatPhoneInput"
              @focus="showSuggestions = true"
              @blur="hideSuggestions"
              maxlength="14"
            />
          </div>
          
          <div v-if="showSuggestions && !isLoading" class="suggestions">
            <div class="suggestion-title">Доступные коды операторов:</div>
            <div class="suggestion-codes">
              <span class="code-badge">29</span>
              <span class="code-badge">33</span>
              <span class="code-badge">44</span>
              <span class="code-badge">25</span>
            </div>
            <div class="suggestion-example">
              Пример: 44 458-69-48 → +375 44 458-69-48
            </div>
          </div>
        </div>
        
        <div v-if="phoneError" class="field-error">
          <span class="error-icon">⚠️</span>
          {{ phoneError }}
        </div>
        
        <button 
          type="submit" 
          class="submit-btn"
          :disabled="!isPhoneValid || isLoading"
        >
          <span v-if="isLoading" class="btn-spinner"></span>
          <span v-else>Продолжить</span>
        </button>
      </form>
      
      <div v-if="error" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = 'X-CSRFToken'
  axios.defaults.withCredentials = true
  
  export default {
    name: 'PhoneRegistration',
    data() {
      return {
        phoneDisplay: '',
        phoneRaw: '',
        isLoading: false,
        error: null,
        phoneError: null,
        showSuggestions: false,
        hideTimeout: null
      }
    },
    computed: {
      // Формируем полный номер в формате +375XXXXXXXXX
      fullPhoneNumber() {
        const cleaned = this.phoneRaw.replace(/\D/g, '')
        if (cleaned.length === 0) return ''
        // Проверяем что есть код оператора
        if (cleaned.length < 2) return ''
        // Формируем +375 + код + остальные цифры
        const operator = cleaned.slice(0, 2)
        const rest = cleaned.slice(2)
        return '+375' + operator + rest
      },
      isPhoneValid() {
        if (!this.phoneRaw) return false
        const cleaned = this.phoneRaw.replace(/\D/g, '')
        // Должно быть 9 цифр: 2 (код) + 7 (номер)
        return cleaned.length === 9
      }
    },
    methods: {
      formatPhoneInput() {
        // Убираем все не цифры
        let cleaned = this.phoneDisplay.replace(/\D/g, '')
        
        // Ограничиваем длину (максимум 9 цифр)
        if (cleaned.length > 9) {
          cleaned = cleaned.slice(0, 9)
        }
        
        this.phoneRaw = cleaned
        
        // Форматируем для отображения: XX XXX-XX-XX
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
        
        // Валидация
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
      
      hideSuggestions() {
        this.hideTimeout = setTimeout(() => {
          this.showSuggestions = false
        }, 300)
      },
      
      async submitPhone() {
        if (!this.isPhoneValid) {
          this.error = 'Пожалуйста, введите корректный номер телефона'
          return
        }
        
        this.isLoading = true
        this.error = null
        
        const phoneToSend = this.fullPhoneNumber
        console.log('Sending phone:', phoneToSend)
        
        try {
          const response = await axios.post('/api/register/', {
            phone_number: phoneToSend
          })
          
          console.log('Register response:', response.data)
          
          if (response.data.success) {
            this.$emit('verified', response.data)
          } else {
            this.error = response.data.error || 'Ошибка регистрации'
          }
        } catch (error) {
          console.error('Register error:', error)
          console.error('Response data:', error.response?.data)
          
          if (error.response) {
            this.error = error.response.data.error || 
                        error.response.data.reason ||
                        error.response.data.detail ||
                        'Ошибка сервера'
          } else {
            this.error = 'Ошибка соединения с сервером'
          }
        } finally {
          this.isLoading = false
        }
      }
    },
    watch: {
      phoneRaw() {
        this.validatePhone()
      }
    }
  }
  </script>
  
  <style scoped>
  .phone-registration {
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
  
  .step-description {
    color: #666;
    margin-bottom: 25px;
    font-size: 16px;
    line-height: 1.5;
  }
  
  .hint {
    color: #999;
    font-size: 14px;
  }
  
  .phone-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .input-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .input-group label {
    font-weight: 600;
    color: #333;
    font-size: 14px;
  }
  
  .phone-input-wrapper {
    display: flex;
    align-items: center;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    overflow: hidden;
    transition: border-color 0.3s;
  }
  
  .phone-input-wrapper:focus-within {
    border-color: #1a237e;
  }
  
  .country-code {
    padding: 14px 12px;
    background: #f5f5f5;
    font-weight: 600;
    color: #1a237e;
    font-size: 18px;
    border-right: 1px solid #e0e0e0;
    flex-shrink: 0;
  }
  
  .phone-input-wrapper input {
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
  
  .phone-input-wrapper input::placeholder {
    color: #bbb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: normal;
    font-size: 16px;
  }
  
  .phone-input-wrapper input:disabled {
    opacity: 0.7;
    background: #f5f5f5;
  }
  
  .suggestions {
    background: #f8f9ff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    animation: slideDown 0.2s ease;
  }
  
  .suggestion-title {
    color: #666;
    margin-bottom: 8px;
  }
  
  .suggestion-codes {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  
  .code-badge {
    background: #1a237e;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
  }
  
  .suggestion-example {
    color: #999;
    font-size: 13px;
  }
  
  .field-error {
    color: #c62828;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: -10px;
  }
  
  .error-icon {
    font-size: 18px;
  }
  
  .submit-btn {
    padding: 16px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  
  .submit-btn:not(:disabled):active {
    transform: scale(0.98);
  }
  
  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .submit-btn:hover:not(:disabled) {
    box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
  }
  
  .btn-spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  .error-message {
    margin-top: 20px;
    padding: 14px;
    background: #fde8e8;
    border-left: 4px solid #e53935;
    border-radius: 8px;
    color: #c62828;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
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
    
    .step-description {
      font-size: 14px;
    }
    
    .country-code {
      padding: 12px 10px;
      font-size: 16px;
    }
    
    .phone-input-wrapper input {
      font-size: 16px;
      padding: 12px 14px;
    }
    
    .submit-btn {
      font-size: 16px;
      padding: 14px;
    }
  }
  </style>