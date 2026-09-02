<!-- frontend/src/components/common/Header.vue -->
<template>
  <header class="header" v-if="showHeader">
    <div class="header-container">
      <div class="logo" @click="goHome">
        <span class="logo-icon">🏢</span>
        <span class="logo-text">Электронный пропуск</span>
      </div>
      
      <nav class="nav-menu" :class="{ 'nav-open': isMenuOpen }">
        <!-- Показываем только для подрядчиков -->
        <router-link v-if="userRole === 'contractor'" to="/dashboard" class="nav-link" @click="closeMenu">
          <span class="nav-icon">👤</span>
          <span>Мой пропуск</span>
        </router-link>
        
        <!-- Показываем для охранников и админов -->
        <router-link v-if="userRole === 'guard' || userRole === 'admin'" to="/dashboard-admin" class="nav-link" @click="closeMenu">
          <span class="nav-icon">🛡️</span>
          <span>Панель управления</span>
        </router-link>
        
        <!-- Показываем для охранников отдельную вкладку -->
        <router-link v-if="userRole === 'guard'" to="/guard" class="nav-link" @click="closeMenu">
          <span class="nav-icon">📷</span>
          <span>Охрана</span>
        </router-link>
        
        <button class="nav-link logout-link" @click="handleLogout">
          <span class="nav-icon">🚪</span>
          <span>Выйти</span>
        </button>
      </nav>
      
      <!-- Профиль пользователя -->
      <div class="user-profile" v-if="userData">
        <div class="user-info">
          <span class="user-name">{{ userData.full_name || userData.first_name }}</span>
          <span class="user-role-badge" :class="userRole">
            {{ userRole === 'guard' ? '🛡️ Охранник' : userRole === 'admin' ? '⚙️ Админ' : '👤 Подрядчик' }}
          </span>
        </div>
        <div class="user-avatar" @click="openUserModal">
          <img 
            v-if="userData.photo" 
            :src="getPhotoUrl(userData.photo)" 
            :alt="userData.full_name"
            class="avatar-image"
            @error="handleAvatarError"
          />
          <span v-else class="avatar-placeholder">
            {{ getInitials(userData.full_name || userData.first_name) }}
          </span>
        </div>
      </div>
      
      <button class="menu-toggle" @click="toggleMenu" aria-label="Меню">
        <span class="menu-icon" :class="{ 'menu-open': isMenuOpen }">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>
    </div>

    <!-- Модальное окно с информацией о пользователе -->
    <div v-if="showUserModal" class="user-modal-overlay" @click.self="closeUserModal">
      <div class="user-modal">
        <div class="user-modal-header">
          <h3>👤 Профиль</h3>
          <button class="close-btn" @click="closeUserModal">✕</button>
        </div>
        <div class="user-modal-body">
          <div class="user-modal-avatar">
            <img 
              v-if="userData?.photo" 
              :src="getPhotoUrl(userData.photo)" 
              :alt="userData.full_name"
              class="modal-avatar-image"
              @error="handleAvatarError"
            />
            <span v-else class="modal-avatar-placeholder">
              {{ getInitials(userData?.full_name || userData?.first_name) }}
            </span>
          </div>
          <div class="user-modal-info">
            <p><strong>ФИО:</strong> {{ userData?.full_name || 'Не указано' }}</p>
            <p><strong>Телефон:</strong> {{ userData?.phone_number || 'Не указан' }}</p>
            <p><strong>Роль:</strong> {{ userRole === 'guard' ? '🛡️ Охранник' : userRole === 'admin' ? '⚙️ Администратор' : '👤 Подрядчик' }}</p>
            <p v-if="userData?.organization"><strong>Организация:</strong> {{ userData.organization }}</p>
          </div>
        </div>
        <div class="user-modal-footer">
          <button class="logout-btn-modal" @click="handleLogout">🚪 Выйти</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'Header',
  data() {
    return {
      isMenuOpen: false,
      userRole: null,
      userData: null,
      showHeader: false,
      showUserModal: false
    }
  },
  mounted() {
    this.checkAuth()
  },
  methods: {
    checkAuth() {
      const isAuth = localStorage.getItem('isAuthenticated')
      const role = localStorage.getItem('userRole')
      const userDataStr = localStorage.getItem('userData')
      
      if (isAuth === 'true' && role && userDataStr) {
        try {
          this.userRole = role
          this.userData = JSON.parse(userDataStr)
          this.showHeader = true
        } catch (e) {
          console.error('Ошибка парсинга userData:', e)
          this.showHeader = false
        }
      } else {
        this.showHeader = false
      }
    },
    
    getPhotoUrl(photoPath) {
      if (!photoPath) return ''
      if (photoPath.startsWith('http')) return photoPath
      if (photoPath.startsWith('/media/')) {
        return `http://localhost:8000${photoPath}`
      }
      return `http://localhost:8000/media/${photoPath}`
    },
    
    getInitials(name) {
      if (!name) return '👤'
      const parts = name.trim().split(' ')
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase()
      }
      return name.slice(0, 2).toUpperCase()
    },
    
    handleAvatarError(e) {
      e.target.style.display = 'none'
      const parent = e.target.parentElement
      const placeholder = parent?.querySelector('.avatar-placeholder')
      if (placeholder) {
        placeholder.style.display = 'flex'
      }
    },
    
    toggleMenu() {
      this.isMenuOpen = !this.isMenuOpen
    },
    
    closeMenu() {
      this.isMenuOpen = false
    },
    
    goHome() {
      this.$router.push('/')
    },
    
    openUserModal() {
      this.showUserModal = true
      this.closeMenu()
    },
    
    closeUserModal() {
      this.showUserModal = false
    },
    
    handleLogout() {
      if (confirm('Вы уверены, что хотите выйти?')) {
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('userRole')
        localStorage.removeItem('userData')
        this.showHeader = false
        this.showUserModal = false
        this.$router.push('/')
      }
    }
  },
  watch: {
    '$route.path'() {
      this.checkAuth()
    }
  }
}
</script>

<style scoped>
.header {
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  flex-shrink: 0;
}

.logo:hover {
  opacity: 0.9;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  white-space: nowrap;
}

.nav-menu {
  display: flex;
  gap: 20px;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.logout-link {
  color: rgba(255, 200, 200, 0.9);
}

.logout-link:hover {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
}

.nav-icon {
  font-size: 20px;
}

/* Профиль пользователя */
.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 12px 4px 16px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.3s;
  flex-shrink: 0;
}

.user-profile:hover {
  background: rgba(255, 255, 255, 0.2);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.2;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.user-role-badge {
  font-size: 11px;
  opacity: 0.8;
  color: rgba(255, 255, 255, 0.9);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 14px;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0d47a1, #1a237e);
}

.menu-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
}

.menu-icon {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 28px;
}

.menu-icon span {
  display: block;
  height: 3px;
  background: white;
  border-radius: 3px;
  transition: all 0.3s;
}

.menu-icon.menu-open span:nth-child(1) {
  transform: rotate(45deg) translate(5px, 6px);
}

.menu-icon.menu-open span:nth-child(2) {
  opacity: 0;
}

.menu-icon.menu-open span:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -6px);
}

/* Модальное окно профиля */
.user-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.user-modal {
  background: white;
  border-radius: 16px;
  max-width: 400px;
  width: 100%;
  overflow: hidden;
  animation: slideIn 0.3s ease;
}

.user-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.user-modal-header h3 {
  margin: 0;
  font-size: 20px;
  color: #1a237e;
}

.user-modal-header .close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  transition: transform 0.3s;
}

.user-modal-header .close-btn:hover {
  transform: rotate(90deg);
}

.user-modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.user-modal-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #1a237e;
  flex-shrink: 0;
}

.modal-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #1a237e, #0d47a1);
}

.user-modal-info {
  width: 100%;
}

.user-modal-info p {
  margin: 8px 0;
  color: #333;
  font-size: 14px;
}

.user-modal-info p strong {
  color: #1a237e;
}

.user-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
}

.logout-btn-modal {
  padding: 10px 30px;
  background: #fce4ec;
  color: #c62828;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logout-btn-modal:hover {
  background: #f44336;
  color: white;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-30px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .header-container {
    padding: 10px 15px;
    flex-wrap: wrap;
  }
  
  .logo-text {
    font-size: 18px;
  }
  
  .menu-toggle {
    display: block;
  }
  
  .nav-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    flex-direction: column;
    padding: 20px;
    gap: 10px;
    transform: translateY(-120%);
    transition: transform 0.3s ease;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    z-index: 999;
  }
  
  .nav-menu.nav-open {
    transform: translateY(0);
  }
  
  .nav-link {
    width: 100%;
    padding: 12px 16px;
    justify-content: center;
    font-size: 18px;
  }
  
  .user-profile {
    padding: 4px 8px;
  }
  
  .user-info {
    display: none;
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
  }
}

@media (max-width: 480px) {
  .logo-icon {
    font-size: 24px;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .nav-link {
    font-size: 16px;
    padding: 10px 14px;
  }
  
  .menu-icon {
    width: 24px;
  }
  
  .user-modal {
    max-width: 95%;
  }
}
</style>