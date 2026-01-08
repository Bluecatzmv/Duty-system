import axios from 'axios'

const request = axios.create({
    baseURL: '/api', 
    timeout: 5000
})

// 请求拦截器：自动带上 Token
request.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
}, error => {
    return Promise.reject(error)
})

// 响应拦截器：自动处理 401 过期
request.interceptors.response.use(response => {
    return response.data
}, error => {
    if (error.response && error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user_role')
        window.location.href = '/'
    }
    return Promise.reject(error)
})

export default request
