<!-- frontend/src/views/AdminView.vue -->
<template>
  <div v-if="!isAuthorized" class="unauthorized">
    <div class="unauthorized-container">
      <div class="lock-icon">🔒</div>
      <h2>Доступ запрещен</h2>
      <p>У вас нет прав для просмотра этой страницы</p>
      <button class="go-home-btn" @click="goHome">На главную</button>
    </div>
  </div>
  
  <div v-else class="admin-view">
    <div class="admin-container">
      <div class="header-section">
        <h1>⚙️ Панель управления</h1>
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
      </div>

      <!-- Вкладка: Подрядчики -->
      <div v-if="activeTab === 'contractors'" class="tab-content">
        <div class="section-header">
          <h2>👥 Список подрядчиков</h2>
          <button class="add-btn" @click="showAddModal = true">
            ➕ Добавить подрядчика
          </button>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Телефон</th>
                <th>Код доступа</th>
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
                  <span v-if="contractor.access_code" class="access-code-badge">
                    {{ contractor.access_code }}
                  </span>
                  <span v-else class="no-code">—</span>
                </td>
                <td>
                  <span class="status-badge" :class="contractor.is_verified ? 'verified' : 'pending'">
                    {{ contractor.is_verified ? '✅ Верифицирован' : '⏳ Ожидает' }}
                  </span>
                </td>
                <td>
                  <div class="photo-cell" @click="openPhotoModal(contractor)">
                    <img 
                      v-if="contractor.photo" 
                      :src="getImageUrl(contractor.photo)" 
                      class="mini-photo"
                      @error="handleImageError"
                      :alt="contractor.full_name"
                    />
                    <span v-else class="no-photo-icon">📷</span>
                  </div>
                </td>
                <td>
                  <button class="action-btn delete" @click="deleteContractor(contractor.id)">🗑️</button>
                </td>
              </tr>
              <tr v-if="contractors.length === 0">
                <td colspan="6" class="empty-state">
                  <span class="empty-icon">📭</span>
                  <p>Нет подрядчиков</p>
                  <p class="empty-hint">Нажмите "Добавить подрядчика" чтобы создать</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Вкладка: Списки доступа -->
      <div v-if="activeTab === 'access'" class="tab-content">
        <div class="section-header">
          <h2>📋 Списки доступа</h2>
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
                <th>Код доступа</th>
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
                  <span v-if="item.contractor_info?.access_code" class="access-code-badge">
                    {{ item.contractor_info.access_code }}
                  </span>
                  <span v-else class="no-code">—</span>
                </td>
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
                <td colspan="6" class="empty-state">Нет записей</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Вкладка: Логи -->
      <div v-if="activeTab === 'logs'" class="tab-content">
        <div class="section-header">
          <h2>📊 История проходов</h2>
          <div class="date-selector">
            <input type="date" v-model="selectedDate" @change="loadLogs" />
          </div>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Время</th>
                <th>Подрядчик</th>
                <th>Телефон</th>
                <th>Способ</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in accessLogs" :key="log.id">
                <td>{{ formatDate(log.scanned_at) }}</td>
                <td>{{ log.contractor_info?.full_name || 'Не указано' }}</td>
                <td>{{ log.contractor_info?.phone_number || '-' }}</td>
                <td>
                  <span class="method-badge" :class="log.access_method">
                    {{ log.access_method === 'qr' ? '📷 QR' : '🔑 Код' }}
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="log.is_successful ? 'verified' : 'banned'">
                    {{ log.is_successful ? '✅ Успешно' : '❌ Отказ' }}
                  </span>
                </td>
              </tr>
              <tr v-if="accessLogs.length === 0">
                <td colspan="5" class="empty-state">Нет записей</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
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
              placeholder="+375 (29) 123-45-67"
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

    <!-- Модальное окно для увеличения фото -->
    <div v-if="showPhotoModal" class="photo-modal" @click="closePhotoModal">
      <div class="photo-modal-content" @click.stop>
        <button class="modal-close-btn" @click="closePhotoModal">✕</button>
        <img 
          :src="getImageUrl(selectedContractor?.photo)" 
          :alt="selectedContractor?.full_name"
          class="modal-photo"
          @error="handleImageError"
        />
        <div class="modal-photo-info">
          <p class="modal-photo-name">{{ selectedContractor?.full_name }}</p>
          <p class="modal-photo-phone">{{ selectedContractor?.phone_number }}</p>
          <p v-if="selectedContractor?.access_code" class="modal-photo-code">
            🔑 Код доступа: <strong>{{ selectedContractor.access_code }}</strong>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
axios.defaults.withCredentials = true

// Базовый URL для API
const API_BASE_URL = 'http://localhost:8000'

export default {
  name: 'AdminView',
  data() {
    return {
      isAuthorized: false,
      userRole: null,
      
      activeTab: 'contractors',
      showAddModal: false,
      isLoading: false,
      selectedDate: new Date().toISOString().split('T')[0],
      
      allUsers: [],
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
      
      showPhotoModal: false,
      selectedContractor: null
    }
  },
  mounted() {
    const isAuth = localStorage.getItem('isAuthenticated')
    const userRole = localStorage.getItem('userRole')
    
    if (isAuth === 'true' && (userRole === 'guard' || userRole === 'admin')) {
      this.isAuthorized = true
      this.userRole = userRole
      
      this.loadData()
      this.getCsrfToken()
    } else {
      this.isAuthorized = false
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
      if (cookieValue) {
        axios.defaults.headers.common['X-CSRFToken'] = cookieValue
      }
      return cookieValue
    },
    
    /**
     * Формирует правильный URL для изображения
     * Всегда возвращает URL с localhost:8000
     */
    getImageUrl(photoPath) {
      if (!photoPath) return ''
      
      // Если это уже полный URL с localhost
      if (photoPath.startsWith('http://localhost:8000')) {
        return photoPath
      }
      
      // Если это уже полный URL с другим доменом
      if (photoPath.startsWith('http')) {
        return photoPath
      }
      
      // Если путь начинается с /media/
      if (photoPath.startsWith('/media/')) {
        return `${API_BASE_URL}${photoPath}`
      }
      
      // Для всех остальных случаев
      return `${API_BASE_URL}/media/${photoPath}`
    },
    
    handleImageError(e) {
      console.log('❌ Ошибка загрузки фото:', e.target.src)
      e.target.style.display = 'none'
      const parent = e.target.parentElement
      const noPhotoIcon = parent?.querySelector('.no-photo-icon')
      if (noPhotoIcon) {
        noPhotoIcon.style.display = 'block'
      }
    },
    
    goHome() {
      this.$router.push('/')
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
        const response = await axios.get(`${API_BASE_URL}/api/contractors/`)
        this.allUsers = response.data.results || response.data || []
        
        console.log('📊 Все пользователи:', this.allUsers.length)
        
        // Фильтруем только подрядчиков
        this.contractors = this.allUsers.filter(user => {
          if (user.role === 'contractor') return true
          if (!user.role) {
            if (user.is_superuser) return false
            return true
          }
          if (user.role === 'guard' || user.role === 'admin') return false
          return true
        })
        
        console.log('✅ Отфильтровано подрядчиков:', this.contractors.length)
      } catch (error) {
        console.error('❌ Ошибка загрузки подрядчиков:', error)
      }
    },
    
    async loadAccessList() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/access-lists/`, {
          params: { date: this.selectedDate }
        })
        this.accessList = response.data.results || response.data || []
      } catch (error) {
        console.error('Ошибка загрузки списка доступа:', error)
      }
    },
    
    async loadLogs() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/access-logs/`, {
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
        formData.append('role', 'contractor')
        if (this.newContractor.patronymic) {
          formData.append('patronymic', this.newContractor.patronymic)
        }
        if (this.newContractor.photo) {
          formData.append('photo', this.newContractor.photo)
        }
        
        const csrfToken = this.getCsrfToken()
        
        const response = await axios.post(`${API_BASE_URL}/api/contractors/`, formData, {
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
          `${API_BASE_URL}/api/access-lists/${item.id}/toggle_access/`,
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
        await axios.delete(`${API_BASE_URL}/api/contractors/${id}/`, {
          headers: { 'X-CSRFToken': csrfToken }
        })
        await this.loadContractors()
        alert('✅ Подрядчик удален')
      } catch (error) {
        console.error('Ошибка удаления:', error)
        alert('❌ Ошибка удаления')
      }
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
    },
    
    openPhotoModal(contractor) {
      if (!contractor?.photo) {
        console.log('Нет фото для увеличения')
        return
      }
      this.selectedContractor = contractor
      this.showPhotoModal = true
      document.body.style.overflow = 'hidden'
    },
    
    closePhotoModal() {
      this.showPhotoModal = false
      this.selectedContractor = null
      document.body.style.overflow = ''
    }
  },
  beforeUnmount() {
    document.body.style.overflow = ''
  }
}
</script>

<style scoped>
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
  min-width: 700px;
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
  white-space: nowrap;
}

.data-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e0e0e0;
  vertical-align: middle;
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
  white-space: nowrap;
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

.access-code-badge {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 18px;
  color: #1a237e;
  background: #e8eaf6;
  padding: 2px 10px;
  border-radius: 6px;
  letter-spacing: 2px;
}

.no-code {
  color: #ccc;
}

.photo-cell {
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 60px;
  height: 60px;
  margin: 0 auto;
}

.mini-photo {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e0e0;
  transition: all 0.3s;
}

.mini-photo:hover {
  border-color: #1a237e;
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
}

.no-photo-icon {
  font-size: 28px;
  opacity: 0.4;
}

.method-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.method-badge.qr {
  background: #e3f2fd;
  color: #0d47a1;
}

.method-badge.code {
  background: #f3e5f5;
  color: #6a1b9a;
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

.action-btn:hover {
  transform: scale(1.1);
}

.action-btn.delete {
  background: #fce4ec;
  color: #c62828;
}

.action-btn.ban {
  background: #fce4ec;
  color: #c62828;
}

.action-btn.unban {
  background: #e8f5e9;
  color: #2e7d32;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px 20px !important;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 13px;
  color: #bbb;
  margin-top: 5px;
}

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

@keyframes spin {
  to { transform: rotate(360deg); }
}

.date-selector input {
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.unauthorized {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.unauthorized-container {
  text-align: center;
  background: white;
  border-radius: 16px;
  padding: 40px;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.lock-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.unauthorized-container h2 {
  color: #c62828;
  margin-bottom: 10px;
}

.unauthorized-container p {
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

.modal-photo-code {
  font-size: 16px;
  color: #333;
  margin: 10px 0 0 0;
}

.modal-photo-code strong {
  color: #1a237e;
  font-size: 20px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
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
  
  .photo-modal-content {
    max-width: 95%;
  }
  
  .photo-cell {
    width: 50px;
    height: 50px;
  }
  
  .mini-photo {
    width: 40px;
    height: 40px;
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
    min-width: 500px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px 10px;
  }
  
  .tab-btn {
    font-size: 12px;
    padding: 6px 12px;
  }
  
  .mini-photo {
    width: 36px;
    height: 36px;
  }
  
  .photo-cell {
    width: 44px;
    height: 44px;
  }
  
  .access-code-badge {
    font-size: 14px;
  }
  
  .modal-photo-name {
    font-size: 18px;
  }
  
  .modal-photo-phone {
    font-size: 14px;
  }
}
</style>