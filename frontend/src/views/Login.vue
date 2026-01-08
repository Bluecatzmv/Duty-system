<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NForm, NFormItem, NInput, NButton, NCard } from 'naive-ui'
import request from '../utils/request'

const router = useRouter()
const message = useMessage()

const formValue = ref({ username: '', password: '' })
const loading = ref(false)

const handleLogin = async () => {
    if (!formValue.value.username || !formValue.value.password) {
        message.warning("请输入账号和密码")
        return
    }
    loading.value = true
    try {
        const formData = new FormData()
        formData.append('username', formValue.value.username)
        formData.append('password', formValue.value.password)
        const res = await request.post('/token', formData)
        
        localStorage.setItem('token', res.access_token)
        localStorage.setItem('user_role', res.role)
        message.success("登录成功")
        setTimeout(() => { router.push('/') }, 500)
    } catch (err) {
        message.error("登录失败：账号或密码错误")
    } finally {
        loading.value = false
    }
}

const goBack = () => { router.push('/') }
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-title" style="color: #2c3e50;">技术中心值班系统</div>
        <div class="logo-subtitle" style="color: #7f8c8d;">Duty Roster Management System</div>
      </div>
      
      <n-card class="login-form-card" :bordered="false">
        <n-form size="large">
          <n-form-item :show-label="false">
            <n-input v-model:value="formValue.username" placeholder="请输入账号" />
          </n-form-item>
          <n-form-item :show-label="false">
            <n-input type="password" v-model:value="formValue.password" placeholder="请输入密码" show-password-on="click" />
          </n-form-item>
          
          <n-button type="primary" block color="#2080f0" :loading="loading" @click="handleLogin" style="margin-bottom: 12px; height: 44px; font-weight: bold;">
            立即登录
          </n-button>
          
          <n-button block ghost @click="goBack" style="height: 44px; color: #666;">
            返回排班大屏
          </n-button>
        </n-form>
      </n-card>
   <div class="footer-text" style="color: #aaa;">技术中心值班系统 V1.0</div>
    <div class="footer-text author-signature" style="color: #aaa;">
       SYSTEM DESIGN BY ZMW
     </div>  
    </div>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  /* 这里的背景色设置为纯米白，覆盖任何可能透出的黑色 */
  background: #f5f7fa; 
  display: flex; 
  justify-content: center; 
  align-items: center;
}

.login-box { 
    width: 420px; 
    text-align: center; 
    z-index: 10;
}

.login-header { margin-bottom: 40px; }
.logo-title { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 32px; 
    font-weight: 800;
    letter-spacing: 1px; 
}
.logo-subtitle { 
    font-size: 14px; 
    margin-top: 8px; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
}

.login-form-card { 
    background: #ffffff !important; 
    border-radius: 16px; 
    padding: 30px 20px; 
    /* 加深阴影，让白色卡片在米白背景上更立体 */
    box-shadow: 0 10px 40px rgba(0,0,0,0.08); 
    border: 1px solid #eee;
}

.author-signature {
/* 2. 启用相对定位 */
  position: relative;
  
  /* 3. 强制向上移动 20px (根据需要调整这个数字) */
  top: -20px;
  /* --- 只保留核心的“隐形”机制 --- */
  opacity: 0;             /* 平时透明 */
  cursor: default;        /* 鼠标样式 */
  transition: opacity 0.8s ease; /* 动画效果 */
}

/* 鼠标悬停状态 */
.author-signature:hover {
  opacity: 1; /* 显形 */
}

.footer-text { margin-top: 30px; font-size: 12px; letter-spacing: 1px; }
</style>
