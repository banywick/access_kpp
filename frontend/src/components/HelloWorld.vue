<!-- frontend/src/components/HelloWorld.vue -->
<template>
    <div class="container">
      <h2>Добро пожаловать!</h2>
      <p>Система контроля доступа работает</p>
      <button @click="testApi" class="btn">Проверить API</button>
      <div v-if="apiResponse" class="response">
        <p>{{ apiResponse }}</p>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'HelloWorld',
    data() {
      return {
        apiResponse: null
      }
    },
    methods: {
      async testApi() {
        try {
          const response = await axios.get('/api/contractors/')
          this.apiResponse = '✅ API работает!'
          console.log(response.data)
        } catch (error) {
          this.apiResponse = '❌ Ошибка: ' + error.message
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
  }
  
  .btn {
    background: #4CAF50;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
  }
  
  .btn:hover {
    background: #45a049;
  }
  
  .response {
    margin-top: 20px;
    padding: 10px;
    background: #fff;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
  </style>