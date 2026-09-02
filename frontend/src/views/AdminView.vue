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

      <!-- Дашборд статистики -->
      <div class="dashboard-stats">
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <div class="stat-number">{{ totalContractors }}</div>
            <div class="stat-label">Всего подрядчиков</div>
          </div>
        </div>
        <div class="stat-card territory">
          <div class="stat-icon">📍</div>
          <div class="stat-info">
            <div class="stat-number">{{ contractorsOnTerritory }}</div>
            <div class="stat-label">На территории</div>
          </div>
        </div>
        <div class="stat-card off-territory">
          <div class="stat-icon">🚫</div>
          <div class="stat-info">
            <div class="stat-number">{{ contractorsOffTerritory }}</div>
            <div class="stat-label">Не на территории</div>
          </div>
        </div>
        <div class="stat-card verified">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <div class="stat-number">{{ verifiedContractors }}</div>
            <div class="stat-label">Верифицированы</div>
          </div>
        </div>
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
                <th>Организация</th>
                <th>Код доступа</th>
                <th>Статус</th>
                <th>На территории</th>
                <th>Фото</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="contractor in contractors" :key="contractor.id">
                <td>{{ contractor.full_name || 'Не указано' }}</td>
                <td>{{ contractor.phone_number }}</td>
                <td>{{ contractor.organization || 'Не указана' }}</td>
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
                  <span class="status-badge" :class="getTerritoryStatus(contractor) ? 'on-territory' : 'off-territory'">
                    {{ getTerritoryStatus(contractor) ? '📍 На территории' : '🚫 Не на территории' }}
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
                <td colspan="8" class="empty-state">
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
                <th>Организация</th>
                <th>Код доступа</th>
                <th>Доступ</th>
                <th>Осталось дней</th>
                <th>На территории</th>
                <th>Причина</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in accessList" :key="item.id">
                <td>{{ item.contractor_info?.full_name || 'Не указано' }}</td>
                <td>{{ item.contractor_info?.phone_number || '-' }}</td>
                <td>{{ item.contractor_info?.organization || '-' }}</td>
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
                <td>
                  <span class="days-badge" :class="getDaysClass(getAccessDaysRemaining(item))">
                    {{ getAccessDaysRemaining(item) }}
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="getTerritoryStatus(item.contractor_info) ? 'on-territory' : 'off-territory'">
                    {{ getTerritoryStatus(item.contractor_info) ? '📍 На территории' : '🚫 Не на территории' }}
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
                <td colspan="9" class="empty-state">Нет записей</td>
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
                <th>Организация</th>
                <th>Способ</th>
                <th>Тип</th>
                <th>Охранник</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in accessLogs" :key="log.id">
                <td>{{ formatDate(log.scanned_at) }}</td>
                <td>{{ log.contractor_info?.full_name || 'Не указано' }}</td>
                <td>{{ log.contractor_info?.phone_number || '-' }}</td>
                <td>{{ log.contractor_info?.organization || '-' }}</td>
                <td>
                  <span class="method-badge" :class="log.access_method">
                    {{ log.access_method === 'qr' ? '📷 QR' : '🔑 Код' }}
                  </span>
                </td>
                <td>
                  <span class="type-badge" :class="log.access_type">
                    {{ log.access_type === 'entry' ? '🚗 Въезд' : '🚗 Выезд' }}
                  </span>
                </td>
                <td>
                  <span class="guard-name">
                    {{ log.scanned_by_name || log.scanned_by_info?.full_name || 'Система' }}
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="log.is_successful ? 'verified' : 'banned'">
                    {{ log.is_successful ? '✅ Успешно' : '❌ Отказ' }}
                  </span>
                </td>
              </tr>
              <tr v-if="accessLogs.length === 0">
                <td colspan="8" class="empty-state">Нет записей</td>
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
            <label>Организация *</label>
            <input 
              v-model="newContractor.organization" 
              type="text" 
              placeholder="Название организации"
              required
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
          <p class="modal-photo-org">🏢 {{ selectedContractor?.organization || 'Не указана' }}</p>
          <p class="modal-photo-status">
            {{ getTerritoryStatus(selectedContractor) ? '📍 На территории' : '🚫 Не на территории' }}
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
      
      // Статистика
      totalContractors: 0,
      contractorsOnTerritory: 0,
      contractorsOffTerritory: 0,
      verifiedContractors: 0,
      
      newContractor: {
        phone_number: '',
        first_name: '',
        last_name: '',
        patronymic: '',
        organization: '',
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
    
    getImageUrl(photoPath) {
      if (!photoPath) return ''
      if (photoPath.startsWith('http')) return photoPath
      if (photoPath.startsWith('/media/')) {
        return `${API_BASE_URL}${photoPath}`
      }
      return `${API_BASE_URL}/media/${photoPath}`
    },
    
    getTerritoryStatus(contractor) {
      if (!contractor || !contractor.id) return false
      
      const logs = this.accessLogs.filter(log => 
        log.contractor_info?.id === contractor.id && log.is_successful
      )
      
      if (logs.length === 0) return false
      
      const lastLog = logs.sort((a, b) => 
        new Date(b.scanned_at) - new Date(a.scanned_at)
      )[0]
      
      return lastLog?.access_type === 'entry'
    },
    
    getAccessDaysRemaining(access) {
      if (!access) return '—'
      if (!access.is_allowed) return '❌ Заблокирован'
      if (!access.valid_until) return '—'
      
      const today = new Date()
      const validUntil = new Date(access.valid_until)
      const diffTime = validUntil - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays < 0) return '⏰ Истек'
      return diffDays
    },
    
    getDaysClass(days) {
      if (days === '—' || days === '❌ Заблокирован' || days === '⏰ Истек') return 'expired'
      if (typeof days !== 'number') return ''
      if (days <= 3) return 'danger'
      if (days <= 7) return 'warning'
      return 'success'
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
    
    updateStats() {
      // Общее количество подрядчиков
      this.totalContractors = this.contractors.length
      
      // Количество верифицированных
      this.verifiedContractors = this.contractors.filter(c => c.is_verified).length
      
      // Количество на территории и не на территории
      let onTerritory = 0
      let offTerritory = 0
      
      this.contractors.forEach(contractor => {
        if (this.getTerritoryStatus(contractor)) {
          onTerritory++
        } else {
          offTerritory++
        }
      })
      
      this.contractorsOnTerritory = onTerritory
      this.contractorsOffTerritory = offTerritory
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
        
        this.contractors = this.allUsers.filter(user => {
          if (user.role === 'contractor') return true
          if (!user.role) {
            if (user.is_superuser) return false
            return true
          }
          if (user.role === 'guard' || user.role === 'admin') return false
          return true
        })
        
        // Обновляем статистику
        this.updateStats()
        
        console.log('📊 Все пользователи:', this.allUsers.length)
        console.log('✅ Отфильтровано подрядчиков:', this.contractors.length)
        console.log('📊 На территории:', this.contractorsOnTerritory)
        console.log('📊 Не на территории:', this.contractorsOffTerritory)
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
        console.log('📊 Загружено логов:', this.accessLogs.length)
        
        // Обновляем статистику после загрузки логов
        this.updateStats()
      } catch (error) {
        console.error('Ошибка загрузки логов:', error)
      }
    },
    
    async addContractor() {
      if (!this.newContractor.phone_number || !this.newContractor.first_name || 
          !this.newContractor.last_name || !this.newContractor.organization) {
        alert('Заполните обязательные поля: Телефон, Имя, Фамилия, Организация')
        return
      }
      
      this.isLoading = true
      
      try {
        const formData = new FormData()
        formData.append('phone_number', this.newContractor.phone_number)
        formData.append('first_name', this.newContractor.first_name)
        formData.append('last_name', this.newContractor.last_name)
        formData.append('organization', this.newContractor.organization)
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
        await this.loadAccessList()
        
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
        organization: '',
        photo: null
      }
      this.photoPreview = null
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
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

/* Дашборд статистики */
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  transition: transform 0.3s, box-shadow 0.3s;
  border: 1px solid #e0e0e0;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.stat-card .stat-icon {
  font-size: 32px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
}

.stat-card .stat-info {
  flex: 1;
}

.stat-card .stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #1a237e;
  line-height: 1.2;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 2px;
}

.stat-card.territory .stat-icon {
  background: #e3f2fd;
}
.stat-card.territory .stat-number {
  color: #0d47a1;
}

.stat-card.off-territory .stat-icon {
  background: #f5f5f5;
}
.stat-card.off-territory .stat-number {
  color: #666;
}

.stat-card.verified .stat-icon {
  background: #e8f5e9;
}
.stat-card.verified .stat-number {
  color: #2e7d32;
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
  min-width: 900px;
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

.status-badge.on-territory {
  background: #e3f2fd;
  color: #0d47a1;
}

.status-badge.off-territory {
  background: #f5f5f5;
  color: #666;
}

.days-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
  white-space: nowrap;
}

.days-badge.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.days-badge.warning {
  background: #fff3e0;
  color: #e65100;
}

.days-badge.danger {
  background: #fce4ec;
  color: #c62828;
}

.days-badge.expired {
  background: #f5f5f5;
  color: #999;
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

.type-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.entry {
  background: #e8f5e9;
  color: #2e7d32;
}

.type-badge.exit {
  background: #fce4ec;
  color: #c62828;
}

.guard-name {
  font-weight: 600;
  color: #1a237e;
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

.modal-photo-org {
  font-size: 16px;
  color: #333;
  margin: 5px 0 0 0;
}

.modal-photo-status {
  font-size: 16px;
  color: #1a237e;
  margin: 5px 0 0 0;
  font-weight: 600;
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
  
  .dashboard-stats {
    grid-template-columns: repeat(2, 1fr);
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
    min-width: 600px;
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
  
  .dashboard-stats {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  
  .stat-card {
    padding: 15px;
  }
  
  .stat-card .stat-number {
    font-size: 22px;
  }
  
  .stat-card .stat-icon {
    font-size: 24px;
    width: 40px;
    height: 40px;
  }
}
</style>