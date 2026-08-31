<!-- frontend/src/components/common/Header.vue -->
<template>
    <header class="header">
      <div class="header-container">
        <div class="logo">
          <span class="logo-icon">🏢</span>
          <span class="logo-text">Контроль доступа</span>
        </div>
        
        <nav class="nav-menu" :class="{ 'nav-open': isMenuOpen }">
          <router-link to="/" class="nav-link" @click="closeMenu">
            <span class="nav-icon">📱</span>
            <span>Подрядчику</span>
          </router-link>
          <router-link to="/guard" class="nav-link" @click="closeMenu">
            <span class="nav-icon">🛡️</span>
            <span>Охране</span>
          </router-link>
          <router-link to="/admin" class="nav-link" @click="closeMenu">
            <span class="nav-icon">⚙️</span>
            <span>Админу</span>
          </router-link>
        </nav>
        
        <button class="menu-toggle" @click="toggleMenu" aria-label="Меню">
          <span class="menu-icon" :class="{ 'menu-open': isMenuOpen }">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
      </div>
    </header>
  </template>
  
  <script>
  export default {
    name: 'Header',
    data() {
      return {
        isMenuOpen: false
      }
    },
    methods: {
      toggleMenu() {
        this.isMenuOpen = !this.isMenuOpen
      },
      closeMenu() {
        this.isMenuOpen = false
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
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: bold;
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
  }
  
  .nav-link:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
  }
  
  .nav-link.router-link-active {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }
  
  .nav-icon {
    font-size: 20px;
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
  
  /* Планшеты */
  @media (max-width: 768px) {
    .header-container {
      padding: 12px 15px;
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
  }
  
  /* Смартфоны */
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
  }
  </style>