import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
// 引入字体
import 'vfonts/Lato.css' 
import 'vfonts/FiraCode.css'

const app = createApp(App)

app.use(router) // 挂载路由
app.mount('#app')
