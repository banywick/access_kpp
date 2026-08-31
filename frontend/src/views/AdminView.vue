<!-- frontend/src/views/AdminView.vue -->
<template>
    <div class="admin-view">
      <div class="admin-container">
        <div class="header-section">
          <h1>⚙️ Администрирование</h1>
          <p class="subtitle">Управление списками доступа и подрядчиками</p>
        </div>
  
        <div class="admin-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'contractors' }"
            @click="activeTab = 'contractors'"
          >
            👥 Подрядчики
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'access' }"
            @click="activeTab = 'access'"
          >
            📋 Списки доступа
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'logs' }"
            @click="activeTab = 'logs'"
          >
            📊 Логи
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'upload' }"
            @click="activeTab = 'upload'"
          >
            📤 Загрузка Excel
          </button>
        </div>
  
        <!-- Вкладка: Подрядчики -->
        <div v-if="activeTab === 'contractors'" class="tab-content">
          <div class="section-header">
            <h2>👥 Список подрядчиков</h2>
            <button class="add-btn" @click="showAddModal = true">
              ➕ Добавить подрядчика
            </button>
          </div>
  
          <!-- Таблица подрядчиков -->
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Телефон</th>
                  <th>Статус</th>
                  <th>Фото</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="contractor in contractors" :key="contractor.id">
                  <td>{{ contractor.full_name || 'Не указано' }}</td>
                  <td>{{ contractor.phone_number }}</td>
                  <td>
                    <span class="status-badge" :class="contractor.is_verified ? 'verified' : 'pending'">
                      {{ contractor.is_verified ? '✅ Верифицирован' : '⏳ Ожидает' }}
                    </span>
                  </td>
                  <td>
                    <img 
                      v-if="contractor.photo" 
                      :src="getPhotoUrl(contractor.photo)" 
                      class="mini-photo"
                      @error="(e) => e.target.style.display = 'none'"
                    />
                    <span v-else class="no-photo-icon">📷</span>
                  </td>
                  <td>
                    <button class="action-btn edit" @click="editContractor(contractor)">✏️</button>
                    <button class="action-btn delete" @click="deleteContractor(contractor.id)">🗑️</button>
                    <button class="action-btn qr" @click="generateQR(contractor)">📱</button>
                  </td>
                </tr>
                <tr v-if="contractors.length === 0">
                  <td colspan="5" class="empty-state">Нет подрядчиков</td>
                </tr>
              </tbody>
            </table>
          </div>
  
          <!-- Модальное окно добавления подрядчика -->
          <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
            <div class="modal">
              <div class="modal-header">
                <h2>➕ Добавить подрядчика</h2>
                <button class="close-btn" @click="showAddModal = false">✕</button>
              </div>
              
              <form @submit.prevent="addContractor" class="modal-form">
                <div class="form-group">
                  <label>Номер телефона *</label>
                  <input 
                    v-model="newContractor.phone_number" 
                    type="tel" 
                    placeholder="+375 25 625 84 17"
                    required
                  />
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label>Имя *</label>
                    <input 
                      v-model="newContractor.first_name" 
                      type="text" 
                      placeholder="Иван"
                      required
                    />
                  </div>
                  <div class="form-group">
                    <label>Фамилия *</label>
                    <input 
                      v-model="newContractor.last_name" 
                      type="text" 
                      placeholder="Петров"
                      required
                    />
                  </div>
                </div>
                
                <div class="form-group">
                  <label>Отчество</label>
                  <input 
                    v-model="newContractor.patronymic" 
                    type="text" 
                    placeholder="Иванович"
                  />
                </div>
                
                <div class="form-group">
                  <label>Фото</label>
                  <input 
                    type="file" 
                    accept="image/*"
                    @change="handlePhotoUpload"
                  />
                  <div v-if="photoPreview" class="photo-preview">
                    <img :src="photoPreview" alt="Preview" />
                    <button type="button" class="remove-photo" @click="removePhoto">✕</button>
                  </div>
                </div>
                
                <div class="form-actions">
                  <button type="button" class="cancel-btn" @click="showAddModal = false">Отмена</button>
                  <button type="submit" class="submit-btn" :disabled="isLoading">
                    <span v-if="isLoading" class="spinner"></span>
                    <span v-else>💾 Сохранить</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
  
        <!-- Вкладка: Списки доступа -->
        <div v-if="activeTab === 'access'" class="tab-content">
          <div class="section-header">
            <h2>📋 Списки доступа на сегодня</h2>
            <div class="date-selector">
              <input type="date" v-model="selectedDate" @change="loadAccessList" />
            </div>
          </div>
  
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Подрядчик</th>
                  <th>Телефон</th>
                  <th>Доступ</th>
                  <th>Причина</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in accessList" :key="item.id">
                  <td>{{ item.contractor_info?.full_name || 'Не указано' }}</td>
                  <td>{{ item.contractor_info?.phone_number || '-' }}</td>
                  <td>
                    <span class="status-badge" :class="item.is_allowed ? 'verified' : 'banned'">
                      {{ item.is_allowed ? '✅ Разрешен' : '❌ Запрещен' }}
                    </span>
                  </td>
                  <td>{{ item.ban_reason || '-' }}</td>
                  <td>
                    <button 
                      class="action-btn" 
                      :class="item.is_allowed ? 'ban' : 'unban'"
                      @click="toggleAccess(item)"
                    >
                      {{ item.is_allowed ? '🚫' : '✅' }}
                    </button>
                  </td>
                </tr>
                <tr v-if="accessList.length === 0">
                  <td colspan="5" class="empty-state">Нет записей</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
  
        <!-- Вкладка: Логи -->
        <div v-if="activeTab === 'logs'" class="tab-content">
          <div class="section-header">
            <h2>📊 История проходов</h2>
          </div>
  
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Время</th>
                  <th>Подрядчик</th>
                  <th>Телефон</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in accessLogs" :key="log.id">
                  <td>{{ formatDate(log.scanned_at) }}</td>
                  <td>{{ log.contractor_info?.full_name || 'Не указано' }}</td>
                  <td>{{ log.contractor_info?.phone_number || '-' }}</td>
                  <td>
                    <span class="status-badge" :class="log.is_successful ? 'verified' : 'banned'">
                      {{ log.is_successful ? '✅ Успешно' : '❌ Отказ' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="accessLogs.length === 0">
                  <td colspan="4" class="empty-state">Нет записей</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
  
        <!-- Вкладка: Загрузка Excel -->
        <div v-if="activeTab === 'upload'" class="tab-content">
          <div class="upload-section">
            <h2>📤 Загрузка списка из Excel</h2>
            <p class="upload-hint">
              Загрузите Excel файл (.xlsx, .xls) с колонками: <strong>ФИО</strong> и <strong>Телефон</strong>
            </p>
            
            <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
              <input 
                type="file" 
                ref="fileInput"
                accept=".xlsx,.xls"
                @change="handleFileUpload"
                style="display: none"
              />
              <div class="upload-placeholder" @click="$refs.fileInput.click()">
                <span class="upload-icon">📁</span>
                <p>Нажмите или перетащите файл</p>
                <span class="upload-ext">.xlsx, .xls</span>
              </div>
            </div>
  
            <div v-if="uploadResult" class="upload-result" :class="uploadResult.success ? 'success' : 'error'">
              <h4>{{ uploadResult.success ? '✅ Успешно!' : '❌ Ошибка' }}</h4>
              <p v-if="uploadResult.created">Создано: {{ uploadResult.created }}</p>
              <p v-if="uploadResult.updated">Обновлено: {{ uploadResult.updated }}</p>
              <p v-if="uploadResult.errors && uploadResult.errors.length">
                Ошибки: {{ uploadResult.errors.length }}
                <ul>
                  <li v-for="(error, idx) in uploadResult.errors" :key="idx">{{ error }}</li>
                </ul>
              </p>
              <p v-if="uploadResult.error">{{ uploadResult.error }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  // Настройка axios для CSRF
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = 'X-CSRFToken'
  axios.defaults.withCredentials = true
  
  export default {
    name: 'AdminView',
    data() {
      return {
        activeTab: 'contractors',
        showAddModal: false,
        isLoading: false,
        selectedDate: new Date().toISOString().split('T')[0],
        
        contractors: [],
        accessList: [],
        accessLogs: [],
        
        newContractor: {
          phone_number: '',
          first_name: '',
          last_name: '',
          patronymic: '',
          photo: null
        },
        
        photoPreview: null,
        uploadResult: null
      }
    },
    mounted() {
      this.loadData()
      // Получаем CSRF токен
      this.getCsrfToken()
    },
    methods: {
      getCsrfToken() {
        // Получаем CSRF токен из cookie
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
        if (cookieValue) {
          axios.defaults.headers.common['X-CSRFToken'] = cookieValue
        }
        return cookieValue
      },
      
      getPhotoUrl(photoPath) {
        if (!photoPath) return ''
        if (photoPath.startsWith('http')) return photoPath
        return `http://localhost:8000${photoPath}`
      },
      
      async loadData() {
        await Promise.all([
          this.loadContractors(),
          this.loadAccessList(),
          this.loadLogs()
        ])
      },
      
      async loadContractors() {
        try {
          const response = await axios.get('/api/contractors/')
          this.contractors = response.data.results || response.data || []
        } catch (error) {
          console.error('Ошибка загрузки подрядчиков:', error)
        }
      },
      
      async loadAccessList() {
        try {
          const response = await axios.get('/api/access-lists/', {
            params: { date: this.selectedDate }
          })
          this.accessList = response.data.results || response.data || []
        } catch (error) {
          console.error('Ошибка загрузки списка доступа:', error)
        }
      },
      
      async loadLogs() {
        try {
          const response = await axios.get('/api/access-logs/', {
            params: { date: this.selectedDate }
          })
          this.accessLogs = response.data.results || response.data || []
        } catch (error) {
          console.error('Ошибка загрузки логов:', error)
        }
      },
      
      async addContractor() {
        if (!this.newContractor.phone_number || !this.newContractor.first_name || !this.newContractor.last_name) {
          alert('Заполните обязательные поля: Телефон, Имя, Фамилия')
          return
        }
        
        this.isLoading = true
        
        try {
          const formData = new FormData()
          formData.append('phone_number', this.newContractor.phone_number)
          formData.append('first_name', this.newContractor.first_name)
          formData.append('last_name', this.newContractor.last_name)
          if (this.newContractor.patronymic) {
            formData.append('patronymic', this.newContractor.patronymic)
          }
          if (this.newContractor.photo) {
            formData.append('photo', this.newContractor.photo)
          }
          
          // Получаем CSRF токен
          const csrfToken = this.getCsrfToken()
          
          const response = await axios.post('/api/contractors/', formData, {
            headers: { 
              'Content-Type': 'multipart/form-data',
              'X-CSRFToken': csrfToken
            }
          })
          
          this.showAddModal = false
          this.resetForm()
          await this.loadContractors()
          
          alert('✅ Подрядчик успешно добавлен!')
        } catch (error) {
          console.error('Ошибка добавления:', error)
          let errorMsg = 'Неизвестная ошибка'
          if (error.response) {
            console.error('Response data:', error.response.data)
            errorMsg = error.response.data?.detail || 
                       error.response.data?.error || 
                       JSON.stringify(error.response.data)
          }
          alert('❌ Ошибка добавления: ' + errorMsg)
        } finally {
          this.isLoading = false
        }
      },
      
      async toggleAccess(item) {
        try {
          const csrfToken = this.getCsrfToken()
          const response = await axios.post(
            `/api/access-lists/${item.id}/toggle_access/`, 
            {
              ban_reason: item.is_allowed ? 'Доступ запрещен' : ''
            },
            {
              headers: { 'X-CSRFToken': csrfToken }
            }
          )
          
          const index = this.accessList.findIndex(a => a.id === item.id)
          if (index !== -1) {
            this.accessList[index] = response.data
          }
        } catch (error) {
          console.error('Ошибка изменения доступа:', error)
          alert('❌ Ошибка изменения доступа')
        }
      },
      
      async deleteContractor(id) {
        if (!confirm('Удалить подрядчика?')) return
        
        try {
          const csrfToken = this.getCsrfToken()
          await axios.delete(`/api/contractors/${id}/`, {
            headers: { 'X-CSRFToken': csrfToken }
          })
          await this.loadContractors()
          alert('✅ Подрядчик удален')
        } catch (error) {
          console.error('Ошибка удаления:', error)
          alert('❌ Ошибка удаления')
        }
      },
      
      editContractor(contractor) {
        alert('Редактирование в разработке')
      },
      
      generateQR(contractor) {
        alert(`QR-код для ${contractor.full_name}: ${contractor.qr_code || 'Не сгенерирован'}`)
      },
      
      handlePhotoUpload(event) {
        const file = event.target.files[0]
        if (file) {
          this.newContractor.photo = file
          const reader = new FileReader()
          reader.onload = (e) => {
            this.photoPreview = e.target.result
          }
          reader.readAsDataURL(file)
        }
      },
      
      removePhoto() {
        this.newContractor.photo = null
        this.photoPreview = null
        this.$refs.fileInput.value = ''
      },
      
      handleFileUpload(event) {
        const file = event.target.files[0]
        if (file) {
          this.uploadExcel(file)
        }
      },
      
      handleDrop(event) {
        const file = event.dataTransfer.files[0]
        if (file) {
          this.uploadExcel(file)
        }
      },
      
      async uploadExcel(file) {
        const formData = new FormData()
        formData.append('file', file)
        
        try {
          const csrfToken = this.getCsrfToken()
          const response = await axios.post('/api/upload-excel/', formData, {
            headers: { 
              'Content-Type': 'multipart/form-data',
              'X-CSRFToken': csrfToken
            }
          })
          
          this.uploadResult = response.data
          if (response.data.success) {
            await this.loadContractors()
          }
        } catch (error) {
          this.uploadResult = {
            success: false,
            error: error.response?.data?.error || 'Ошибка загрузки'
          }
        }
      },
      
      resetForm() {
        this.newContractor = {
          phone_number: '',
          first_name: '',
          last_name: '',
          patronymic: '',
          photo: null
        }
        this.photoPreview = null
      },
      
      formatDate(dateString) {
        if (!dateString) return '-'
        try {
          const date = new Date(dateString)
          return date.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })
        } catch {
          return dateString
        }
      }
    }
  }
  </script>
  
  <style scoped>
  /* ... (стили остаются те же) ... */
  .admin-view {
    min-height: 80vh;
    padding: 20px;
  }
  
  .admin-container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 16px;
    padding: 30px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
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
    color: #666;
    font-size: 16px;
  }
  
  .admin-tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
    flex-wrap: wrap;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 10px;
  }
  
  .tab-btn {
    padding: 10px 20px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    color: #666;
    border-radius: 8px;
    transition: all 0.3s;
  }
  
  .tab-btn:hover {
    background: #f5f5f5;
  }
  
  .tab-btn.active {
    background: #1a237e;
    color: white;
  }
  
  .tab-content {
    animation: fadeIn 0.3s ease;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 15px;
  }
  
  .section-header h2 {
    font-size: 20px;
    color: #1a237e;
  }
  
  .add-btn {
    padding: 10px 20px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.3s;
  }
  
  .add-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
  }
  
  .table-container {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
  }
  
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  
  .data-table thead {
    background: #f5f7fa;
  }
  
  .data-table th {
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    color: #333;
    border-bottom: 2px solid #e0e0e0;
  }
  
  .data-table td {
    padding: 12px 15px;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .data-table tbody tr:hover {
    background: #f8f9ff;
  }
  
  .status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
  }
  
  .status-badge.verified {
    background: #e8f5e9;
    color: #2e7d32;
  }
  
  .status-badge.pending {
    background: #fff3e0;
    color: #e65100;
  }
  
  .status-badge.banned {
    background: #fce4ec;
    color: #c62828;
  }
  
  .mini-photo {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .no-photo-icon {
    font-size: 24px;
  }
  
  .action-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    margin: 0 2px;
    transition: all 0.2s;
  }
  
  .action-btn.edit {
    background: #e3f2fd;
    color: #0d47a1;
  }
  
  .action-btn.delete {
    background: #fce4ec;
    color: #c62828;
  }
  
  .action-btn.qr {
    background: #e8f5e9;
    color: #2e7d32;
  }
  
  .action-btn.ban {
    background: #fce4ec;
    color: #c62828;
  }
  
  .action-btn.unban {
    background: #e8f5e9;
    color: #2e7d32;
  }
  
  .action-btn:hover {
    transform: scale(1.1);
  }
  
  .empty-state {
    text-align: center;
    color: #999;
    padding: 30px !important;
  }
  
  /* Модальное окно */
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
  }
  
  .modal {
    background: white;
    border-radius: 16px;
    max-width: 500px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    padding: 30px;
    animation: slideIn 0.3s ease;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .modal-header h2 {
    font-size: 22px;
    color: #1a237e;
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
  }
  
  .modal-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  
  .form-group label {
    font-weight: 600;
    color: #333;
    font-size: 14px;
  }
  
  .form-group input {
    padding: 10px 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.3s;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: #1a237e;
  }
  
  .photo-preview {
    position: relative;
    margin-top: 10px;
    width: 100px;
  }
  
  .photo-preview img {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #e0e0e0;
  }
  
  .remove-photo {
    position: absolute;
    top: -8px;
    right: -8px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: none;
    background: #c62828;
    color: white;
    cursor: pointer;
    font-size: 12px;
  }
  
  .form-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 10px;
  }
  
  .cancel-btn {
    padding: 10px 20px;
    background: #f5f5f5;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .submit-btn {
    padding: 10px 20px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }
  
  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  /* Upload секция */
  .upload-section {
    padding: 20px 0;
  }
  
  .upload-hint {
    color: #666;
    margin-bottom: 20px;
  }
  
  .upload-area {
    border: 2px dashed #e0e0e0;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .upload-area:hover {
    border-color: #1a237e;
    background: #f8f9ff;
  }
  
  .upload-placeholder .upload-icon {
    font-size: 48px;
    display: block;
    margin-bottom: 10px;
  }
  
  .upload-placeholder p {
    color: #666;
    margin: 5px 0;
  }
  
  .upload-ext {
    color: #999;
    font-size: 12px;
  }
  
  .upload-result {
    margin-top: 20px;
    padding: 15px 20px;
    border-radius: 8px;
  }
  
  .upload-result.success {
    background: #e8f5e9;
    border: 1px solid #4CAF50;
  }
  
  .upload-result.error {
    background: #fce4ec;
    border: 1px solid #e53935;
  }
  
  .upload-result ul {
    margin: 10px 0 0 20px;
  }
  
  .date-selector input {
    padding: 8px 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes slideIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @media (max-width: 768px) {
    .admin-container {
      padding: 20px;
    }
    
    .admin-tabs {
      gap: 5px;
    }
    
    .tab-btn {
      font-size: 14px;
      padding: 8px 14px;
    }
    
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .section-header {
      flex-direction: column;
      align-items: stretch;
    }
    
    .modal {
      padding: 20px;
    }
  }
  
  @media (max-width: 480px) {
    .admin-view {
      padding: 10px;
    }
    
    .admin-container {
      padding: 15px;
    }
    
    .header-section h1 {
      font-size: 20px;
    }
    
    .data-table {
      font-size: 12px;
    }
    
    .data-table th,
    .data-table td {
      padding: 8px 10px;
    }
    
    .tab-btn {
      font-size: 12px;
      padding: 6px 12px;
    }
  }
  </style>