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
      
      <div class="footer-text" style="color: #aaa;">SECURE ACCESS V3.3</div>
        <div class="author-signature">
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
  margin-top: 5px;
  font-size: 10px;
  letter-spacing: 2px;
  font-family: 1px; /* 代码字体 */
/* 关键点 1：平时完全透明，但仍然占据空间，等待鼠标触发 */
  opacity: 0;
  cursor: default;        /* 鼠标放上去保持箭头，不变成手指，更隐蔽 */
  
  /* 核心：平时状态的颜色（极暗，接近背景色） */
  color: #aaa; 
  
  /* 核心：平滑过渡动画 0.8秒 */
  transition: opacity 0.8s ease, text-shadow 0.8s ease;
}

/* 鼠标放上去的状态 */
.author-signature:hover {
  opacity: 1;
  
  /* 可选：加一点文字荧光辉光效果 */
  text-shadow: 0 0 8px rgba(175, 238, 238, 0.6);
}

.footer-text { margin-top: 30px; font-size: 12px; letter-spacing: 1px; }
</style>
