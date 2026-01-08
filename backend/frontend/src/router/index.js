import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Stats from '../views/Stats.vue'
import Compensatory from '../views/Compensatory.vue' // 新增

const routes = [
    { path: '/', name: 'Dashboard', component: Dashboard },
    { path: '/login', name: 'Login', component: Login },
    { path: '/stats', name: 'Stats', component: Stats },
    { path: '/compensatory', name: 'Compensatory', component: Compensatory } // 新增路由
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
