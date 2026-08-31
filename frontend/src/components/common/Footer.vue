<!-- frontend/src/components/common/Footer.vue -->
<template>
    <footer class="footer">
      <div class="footer-container">
        <p>&copy; 2024 Система контроля доступа</p>
        <p class="footer-version">v1.0.0</p>
      </div>
    </footer>
  </template>
  
  <script>
  export default {
    name: 'Footer'
  }
  </script>
  
  <style scoped>
  .footer {
    background: #1a237e;
    color: rgba(255, 255, 255, 0.7);
    padding: 15px 20px;
    margin-top: auto;
  }
  
  .footer-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
  }
  
  .footer-version {
    font-size: 12px;
    opacity: 0.6;
  }
  
  @media (max-width: 480px) {
    .footer {
      padding: 12px 15px;
    }
    
    .footer-container {
      flex-direction: column;
      gap: 5px;
      text-align: center;
      font-size: 12px;
    }
  }
  </style>