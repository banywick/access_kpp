<!-- frontend/src/components/common/Header.vue -->
<template>
  <header class="header" v-if="showHeader">
    <div class="header-container">
      <div class="header-left">
        <div class="logo" @click="goHome">
          <span class="logo-icon">🏢</span>
          <span class="logo-text">Электронный пропуск</span>
        </div>
      </div>
      
      <div class="header-center">
        <nav class="nav-menu" :class="{ 'nav-open': isMenuOpen }">
          <router-link v-if="userRole === 'contractor'" to="/dashboard" class="nav-link" @click="closeMenu">
            <span class="nav-icon">👤</span>
            <span>Мой пропуск</span>
          </router-link>
          
          <router-link v-if="userRole === 'guard' || userRole === 'admin'" to="/dashboard-admin" class="nav-link" @click="closeMenu">
            <span class="nav-icon">🛡️</span>
            <span>Панель управления</span>
          </router-link>
          
          <router-link v-if="userRole === 'guard'" to="/guard" class="nav-link" @click="closeMenu">
            <span class="nav-icon">📷</span>
            <span>Охрана</span>
          </router-link>
          
          <button class="nav-link logout-link" @click="handleLogout">
            <span class="nav-icon">🚪</span>
            <span>Выйти</span>
          </button>
        </nav>
      </div>
      
      <div class="header-right">
        <div class="user-profile" v-if="userData" @click="openUserModal">
          <div class="user-avatar">
            <img 
              v-if="userData.photo_url || userData.photo" 
              :src="getImageUrl(userData.photo_url || userData.photo)" 
              :alt="userData.full_name || userData.first_name"
              class="avatar-image"
              @error="handleAvatarError"
            />
            <span v-else class="avatar-placeholder">
              {{ getInitials(userData.full_name || userData.first_name || 'Пользователь') }}
            </span>
          </div>
          <div class="user-info">
            <span class="user-name">{{ userData.full_name || userData.first_name || 'Пользователь' }}</span>
            <span class="user-phone">{{ userData.phone || userData.phone_number || '' }}</span>
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
    </div>

    <!-- Модальное окно профиля -->
    <div v-if="showUserModal" class="user-modal-overlay" @click.self="closeUserModal">
      <div class="user-modal">
        <div class="user-modal-header">
          <h3>👤 Профиль</h3>
          <button class="close-btn" @click="closeUserModal">✕</button>
        </div>
        <div class="user-modal-body">
          <div class="user-modal-avatar">
            <img 
              v-if="userData?.photo_url || userData?.photo" 
              :src="getImageUrl(userData?.photo_url || userData?.photo)" 
              :alt="userData.full_name"
              class="modal-avatar-image"
              @error="handleAvatarError"
            />
            <span v-else class="modal-avatar-placeholder">
              {{ getInitials(userData?.full_name || userData?.first_name || 'Пользователь') }}
            </span>
          </div>
          <div class="user-modal-info">
            <p><strong>ФИО:</strong> {{ userData?.full_name || userData?.first_name || 'Не указано' }}</p>
            <p><strong>Телефон:</strong> {{ userData?.phone || userData?.phone_number || 'Не указан' }}</p>
            <p><strong>Роль:</strong> 
              <span v-if="userRole === 'guard'">🛡️ Охранник</span>
              <span v-else-if="userRole === 'admin'">⚙️ Администратор</span>
              <span v-else>👤 Подрядчик</span>
            </p>
            <p v-if="userData?.organization"><strong>Организация:</strong> {{ userData.organization }}</p>
            <p v-if="userData?.is_verified !== undefined">
              <strong>Статус:</strong> 
              <span :style="{ color: userData.is_verified ? '#2e7d32' : '#e65100' }">
                {{ userData.is_verified ? '✅ Верифицирован' : '⏳ Ожидает верификации' }}
              </span>
            </p>
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
    // Закрываем меню при изменении размера окна
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
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
    
    handleResize() {
      // Закрываем меню при переключении на десктопный размер
      if (window.innerWidth > 768 && this.isMenuOpen) {
        this.isMenuOpen = false
      }
    },
    
    getImageUrl(photoPath) {
      if (!photoPath) return ''
      if (photoPath.startsWith('http')) {
        const pathMatch = photoPath.match(/\/media\/.*/)
        if (pathMatch) {
          return pathMatch[0]
        }
        return photoPath
      }
      if (photoPath.startsWith('/media/')) {
        return photoPath
      }
      return `/media/${photoPath}`
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
      // Блокируем скролл при открытом меню на мобильных
      if (this.isMenuOpen && window.innerWidth <= 768) {
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = ''
      }
    },
    
    closeMenu() {
      this.isMenuOpen = false
      document.body.style.overflow = ''
    },
    
    goHome() {
      this.closeMenu()
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
        this.closeMenu()
        this.$router.push('/')
      }
    }
  },
  watch: {
    '$route.path'() {
      this.checkAuth()
      this.closeMenu()
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
  gap: 10px;
  min-height: 60px;
}

/* Левая часть - логотип */
.header-left {
  flex-shrink: 0;
}

/* Центральная часть - навигация */
.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Правая часть - профиль и меню */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
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
  gap: 5px;
  align-items: center;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 8px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
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
  font-size: 18px;
}

/* Профиль пользователя */
.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px 4px 6px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.3s;
  flex-shrink: 0;
}

.user-profile:hover {
  background: rgba(255, 255, 255, 0.2);
}

.user-avatar {
  width: 34px;
  height: 34px;
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
  font-size: 13px;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0d47a1, #1a237e);
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.user-phone {
  font-size: 10px;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

/* Кнопка меню (бургер) */
.menu-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  min-height: 44px;
  min-width: 44px;
  align-items: center;
  justify-content: center;
}

.menu-icon {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 26px;
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
  max-height: 90vh;
  overflow-y: auto;
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
  min-width: 44px;
  min-height: 44px;
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
  min-height: 44px;
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

/* ========== АДАПТИВНОСТЬ ========== */

/* Планшеты (768px - 1024px) */
@media (max-width: 1024px) {
  .header-container {
    padding: 10px 16px;
  }
  
  .nav-link {
    padding: 6px 12px;
    font-size: 14px;
  }
  
  .user-name {
    max-width: 100px;
    font-size: 12px;
  }
  
  .user-phone {
    max-width: 100px;
    font-size: 10px;
  }
}

/* Смартфоны (до 768px) */
@media (max-width: 768px) {
  .header-container {
    padding: 8px 12px;
    min-height: 52px;
    gap: 8px;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .logo-icon {
    font-size: 24px;
  }
  
  .menu-toggle {
    display: flex;
  }
  
  .header-center {
    position: static;
  }
  
  .nav-menu {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    flex-direction: column;
    padding: 80px 20px 30px;
    gap: 8px;
    transform: translateX(100%);
    transition: transform 0.3s ease;
    z-index: 999;
    overflow-y: auto;
    justify-content: flex-start;
  }
  
  .nav-menu.nav-open {
    transform: translateX(0);
  }
  
  .nav-link {
    width: 100%;
    padding: 14px 20px;
    justify-content: center;
    font-size: 18px;
    min-height: 52px;
    border-radius: 12px;
  }
  
  .nav-link:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .nav-icon {
    font-size: 22px;
  }
  
  .user-profile {
    padding: 3px 8px 3px 4px;
    gap: 6px;
  }
  
  .user-avatar {
    width: 30px;
    height: 30px;
  }
  
  .avatar-placeholder {
    font-size: 12px;
  }
  
  .user-info {
    display: none;
  }
  
  /* Кнопка закрытия меню через оверлей */
  .nav-menu::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    z-index: -1;
  }
}

/* Маленькие смартфоны (до 480px) */
@media (max-width: 480px) {
  .header-container {
    padding: 6px 10px;
    min-height: 48px;
  }
  
  .logo-text {
    font-size: 14px;
  }
  
  .logo-icon {
    font-size: 20px;
  }
  
  .user-avatar {
    width: 28px;
    height: 28px;
  }
  
  .menu-icon {
    width: 22px;
  }
  
  .menu-icon span {
    height: 2px;
  }
  
  .nav-link {
    font-size: 16px;
    padding: 12px 16px;
    min-height: 48px;
  }
  
  .nav-icon {
    font-size: 20px;
  }
  
  .user-modal-avatar {
    width: 80px;
    height: 80px;
  }
  
  .modal-avatar-placeholder {
    font-size: 28px;
  }
  
  .user-modal-info p {
    font-size: 13px;
  }
}

/* Очень маленькие экраны (до 360px) */
@media (max-width: 360px) {
  .logo-text {
    font-size: 12px;
  }
  
  .logo-icon {
    font-size: 18px;
  }
  
  .header-container {
    gap: 4px;
    padding: 4px 8px;
  }
  
  .user-avatar {
    width: 24px;
    height: 24px;
  }
  
  .user-profile {
    padding: 2px 4px;
  }
}
</style>