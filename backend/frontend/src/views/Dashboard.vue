<script setup>
import { ref, onMounted, computed } from 'vue' 
import { useRouter } from 'vue-router'
import { 
    useMessage, NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NTag, 
    NCard, NSpin, NModal, NForm, NFormItem, NInput, NSelect, NList, NListItem, 
    NThing, NDatePicker, NRadioGroup, NRadio, NTimePicker, NRadioButton, 
    NDivider, NSwitch, NCheckbox, NTabs, NTabPane, NUpload, NUploadDragger, 
    NIcon, NDataTable, NText, NP
} from 'naive-ui'
import request from '../utils/request'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const router = useRouter()
const message = useMessage()

// ================== 状态定义 ==================
const loading = ref(false)
const calendarEvents = ref([]) 
const holidaysMap = ref({}) 
const currentUser = ref(null) 
const currentViewDate = ref(new Date())

// 管理相关状态
const showUserManageModal = ref(false)
const showHolidayModal = ref(false)
const showWeComModal = ref(false)
const userList = ref([])
const newUserForm = ref({ username: '', real_name: '', password: '', role: 'admin' })

// 企微配置表单
const weComForm = ref({ webhook_url: '', message_template: '', daily_time: null })

// 节假日表单
const newHolidayForm = ref({ 
    rangeDate: null, 
    enableType: true, name: '', type: 'holiday',
    enableGuarantee: false, guaranteeName: ''
})
const holidaysList = ref([])

// 排班编辑
const showEditModal = ref(false)
const editForm = ref({ id: null, staff_name: '', staff_phone: '', date: '', duty_type: '' })

// === 新增：数据导入中心状态 ===
const showImportModal = ref(false)
const importHistory = ref([])
const isOverwriteSchedule = ref(true) // 默认开启覆盖模式
const uploadLoading = ref(false)

// 导入历史表头
const historyColumns = [
    { title: '时间', key: 'import_time', width: 160, render(row){ return new Date(row.import_time).toLocaleString() } },
    { title: '文件名', key: 'filename', ellipsis: { tooltip: true } },
    { title: '类型', key: 'import_type', width: 80, render(row){ return row.import_type === 'schedule' ? '排班' : '通讯录' } },
    { title: '操作人', key: 'operator_name', width: 80 },
    { title: '详情', key: 'description', ellipsis: { tooltip: true } }
]

// ================== 常量定义 ==================
const dutyOptions = [
    { label: '总值班', value: '总值班' }, { label: '技术值班', value: '技术值班' },
    { label: '日间值班', value: '日间值班' }, { label: '夜间值班', value: '夜间值班' },
    { label: '夜间见习', value: '夜间见习' }, { label: '更新值班', value: '更新值班' },
    { label: '更新见习', value: '更新见习' }
]
const dutyColorMap = {
    // 原红色 -> 柔和珊瑚红
    '总值班': '#ef7a7a', 
    // 原深蓝 -> 舒适静谧蓝
    '技术值班': '#6aa1e6', 
    // 原绿色 -> 清新鼠尾草绿
    '日间值班': '#6bc495', 
    // 原橙色 -> 温暖杏橙色
    '夜间值班': '#f2b05e', 
    // 原紫色 -> 雾霾薰衣草紫
    '夜间见习': '#a68cd6', 
    // 原青色 -> 柔和湖水蓝
    '更新值班': '#5dc5d6', 
    // 原灰色 -> 中性灰
    '更新见习': '#a8a8a8'
}
const dutyLabelMap = {
    '总值班': '[总]', '技术值班': '[技]', '日间值班': '[日]', '夜间值班': '[夜]',
    '夜间见习': '[夜见]', '更新值班': '[更]', '更新见习': '[更见]'
}
const dutyRankMap = {
    '总值班': 1, '技术值班': 2, '日间值班': 3, '夜间值班': 4,
    '夜间见习': 5, '更新值班': 6, '更新见习': 7
}

const isAdmin = computed(() => {
    return currentUser.value && (currentUser.value.role === 'admin' || currentUser.value.role === 'super_admin')
})

const formatDateLocal = (dateObj) => {
    const year = dateObj.getFullYear()
    const month = String(dateObj.getMonth() + 1).padStart(2, '0')
    const day = String(dateObj.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}

// ================== 日历配置 ==================
const calendarOptions = ref({
    plugins: [dayGridPlugin, interactionPlugin],
    // === 新增这段代码 ===
    eventDidMount: function(info) {
        // 1. 强制允许浏览器选择
        info.el.style.userSelect = 'text';
        info.el.style.cursor = 'text';
        
        // 2. 关键：禁用 HTML5 原生拖拽
        // 如果不加这句，浏览器会以为你想把这个 div 拖走，从而无法选字
        info.el.setAttribute('draggable', 'false');
        
        // 3. 阻止 FullCalendar 内部对 mousedown 的拦截
        // 这样你的鼠标点击就能穿透给浏览器去处理文字选择
        info.el.onmousedown = (e) => {
            e.stopPropagation(); 
        };
    },
    // ===================
    initialView: 'dayGridMonth',
    locale: 'zh-cn',
    firstDay: 1,
    headerToolbar: { left: 'prev,next today', center: 'title', right: '' },
    eventDisplay: 'block', events: calendarEvents,
    eventOrder: 'rank', datesSet: handleDatesSet, 
    eventClick: handleEventClick,
    dayCellContent: (arg) => {
        const dateStr = formatDateLocal(arg.date)
        const holiday = holidaysMap.value[dateStr]
        const dayNumber = arg.dayNumberText
        
        // 构建 Flex 容器
        let html = `<div class="day-cell-header">`

        // --- 左侧：保障期区域 ---
        html += `<div class="header-left">`
        if (holiday && holiday.is_guarantee) {
            const gName = holiday.guarantee_name || ''
            html += `<span class="tag-icon guarantee-icon">保</span>`
            if (gName) {
                html += `<span class="tag-text guarantee-text">${gName}</span>`
            }
        }
        html += `</div>`

        // --- 右侧：日期 & 节假日区域 ---
        html += `<div class="header-right">`
        if (holiday) {
            if (holiday.type === 'holiday') {
                html += `<div class="holiday-group">`
                html += `<span class="tag-text holiday-text">${holiday.name || ''}</span>`
                html += `<span class="tag-icon holiday-icon">休</span>`
                html += `</div>`
            } else if (holiday.type === 'workday') {
                html += `<div class="holiday-group">`
                html += `<span class="tag-text workday-text">${holiday.name || ''}</span>`
                html += `<span class="tag-icon workday-icon">班</span>`
                html += `</div>`
            }
        }
        html += `<span class="day-number">${dayNumber}</span>`
        html += `</div></div>` // close right & container

        return { html: html }
    }
})

onMounted(async () => { await fetchUserInfo() })


// ================== 基础逻辑 ==================
async function fetchUserInfo() {
    const token = localStorage.getItem('token')
    if(!token) { currentUser.value = null; return }
    try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        currentUser.value = { role: payload.role, username: payload.sub }
    } catch(e) { currentUser.value = null }
}

function handleEventClick(info) {
    // 获取卡片里的数据
    const props = info.event.extendedProps
    const staffName = props.staff_name
    const staffPhone = props.staff_phone || ''
    
    // 组合要复制的文本 (例如: "张三 13800000000")
    const copyText = `${staffName} ${staffPhone}`.trim()

    // === 分流逻辑 ===
    
    // 情况1: 如果不是管理员 -> 执行“点击复制”
    if (!isAdmin.value) { 
        // 使用浏览器剪贴板 API
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(copyText)
                .then(() => {
                    message.success(`已复制: ${copyText}`)
                })
                .catch(() => {
                    message.error("复制失败，请手动输入")
                })
        } else {
            // 兼容非 HTTPS 或旧浏览器
            message.info(`联系信息: ${copyText}`)
        }
        return // 结束，不往下执行登录检查
    }
    
    // 情况2: 如果是管理员 -> 执行“编辑操作” (原有逻辑)
    editForm.value = {
        id: props.id, 
        staff_name: staffName, 
        staff_phone: staffPhone,
        date: info.event.startStr, 
        duty_type: props.duty_type
    }
    showEditModal.value = true
}

function goToLogin() { router.push('/login') }
function handleLogout() { localStorage.clear(); currentUser.value = null; message.success("已退出登录") }

// ================== 账号管理 ==================
async function openUserManage() { showUserManageModal.value = true; userList.value = await request.get('/users/') }
async function createUser() {
    if(!newUserForm.value.username || !newUserForm.value.password) return message.warning("请填写完整")
    try {
        await request.post('/users/', newUserForm.value); message.success("创建成功"); 
        userList.value = await request.get('/users/'); newUserForm.value = { username: '', real_name: '', password: '', role: 'admin' }
    } catch (e) { message.error(e.response?.data?.detail) }
}
async function deleteUser(id) { try { await request.delete(`/users/${id}`); message.success("已删除"); userList.value = await request.get('/users/') } catch {} }

// ================== 节假日管理 ==================
async function openHolidayManage() {
    showHolidayModal.value = true
    const year = currentViewDate.value.getFullYear()
    const month = currentViewDate.value.getMonth() + 1
    holidaysList.value = await request.get('/holidays/', { params: {year, month} })
}

async function createHolidayBatch() {
    if(!newHolidayForm.value.rangeDate) return message.warning("请选择日期范围")
    
    const [startTs, endTs] = newHolidayForm.value.rangeDate
    const fmt = (ts) => formatDateLocal(new Date(ts))
    
    const payload = { 
        start_date: fmt(startTs), 
        end_date: fmt(endTs),
        update_type: newHolidayForm.value.enableType,
        type: newHolidayForm.value.enableType ? newHolidayForm.value.type : null,
        name: newHolidayForm.value.enableType ? newHolidayForm.value.name : null,
        update_guarantee: true,
        is_guarantee: newHolidayForm.value.enableGuarantee,
        guarantee_name: newHolidayForm.value.enableGuarantee ? newHolidayForm.value.guaranteeName : null
    }

    try {
        await request.post('/holidays/batch', payload)
        message.success("设置成功")
        const year = currentViewDate.value.getFullYear()
        const month = currentViewDate.value.getMonth() + 1
        holidaysList.value = await request.get('/holidays/', { params: {year, month} })
        fetchSchedules(year, month)
    } catch (e) { message.error("设置失败: " + e.message) }
}

async function deleteHoliday(id) {
    if (!window.confirm("确定要删除这个节假日/保障期设置吗？")) return
    try { 
        loading.value = true
        await request.delete(`/holidays/${id}`)
        message.success("已删除")
        const year = currentViewDate.value.getFullYear()
        const month = currentViewDate.value.getMonth() + 1
        holidaysList.value = await request.get('/holidays/', { params: {year, month} })
        fetchSchedules(year, month)
    } catch (e) {
        message.error("删除失败: " + (e.response?.data?.detail || e.message))
    } finally {
        loading.value = false
    }
}

// ================== 企微配置 ==================
async function openWeComSettings() {
    showWeComModal.value = true
    try { 
        const res = await request.get('/config/wecom')
        
        // 🔴 核心修复：后端如果返回空字符串 ""，必须转为 null
        // 否则 NTimePicker 会解析失败导致 RangeError 崩溃
        if (!res.daily_time) {
            res.daily_time = null
        }
        
        weComForm.value = res 
    } catch (e) { 
        message.error("获取配置失败") 
    }
}

async function saveWeComSettings() {
    try { await request.post('/config/wecom', weComForm.value); message.success("保存成功"); showWeComModal.value = false } catch (e) { message.error("保存失败") }
}

// === 新增：显式的关闭函数 ===
function closeWeComSettings() {
    showWeComModal.value = false
}
async function testSendWeCom() {
    try {
        const res = await request.post('/notify/send')
        if (res.status === 'success') message.success("发送成功")
        else message.error(res.message)
    } catch (e) { message.error("发送失败") }
}

// ================== 排班编辑 ==================
async function saveScheduleChange() {
    try {
        await request.put(`/schedules/${editForm.value.id}`, editForm.value); message.success("更新成功"); 
        showEditModal.value = false; fetchSchedules(currentViewDate.value.getFullYear(), currentViewDate.value.getMonth() + 1)
    } catch (e) { message.error("更新失败") }
}
async function deleteSchedule() {
    if(!window.confirm("确定删除？")) return
    try { await request.delete(`/schedules/${editForm.value.id}`); message.success("已删除"); showEditModal.value = false; fetchSchedules(currentViewDate.value.getFullYear(), currentViewDate.value.getMonth() + 1) } catch {}
}

// ================== 数据导入/导出 (重构部分) ==================
async function openImportCenter() {
    showImportModal.value = true
    await fetchImportHistory()
}

async function fetchImportHistory() {
    try {
        importHistory.value = await request.get('/imports/history')
    } catch(e) {}
}

async function handleUpload({ file, data }) {
    const formData = new FormData()
    formData.append('file', file.file)
    if (data && data.type === 'schedule') {
        formData.append('is_overwrite', isOverwriteSchedule.value)
    }
    const url = data.type === 'schedule' ? '/schedules/import_excel' : '/contacts/import'
    uploadLoading.value = true
    try {
        const res = await request.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        message.success(res.msg)
        fetchSchedules(currentViewDate.value.getFullYear(), currentViewDate.value.getMonth() + 1)
        fetchImportHistory()
    } catch (e) {
        message.error("导入失败: " + (e.response?.data?.detail || e.message))
    } finally {
        uploadLoading.value = false
    }
}

const customRequest = ({ file, data, onFinish, onError }) => {
    handleUpload({ file, data }).then(onFinish).catch(onError)
}

// ================== 日历逻辑 ==================
function handleDatesSet(arg) {
    const midDate = new Date(arg.start.getTime() + (arg.end.getTime() - arg.start.getTime()) / 2)
    currentViewDate.value = midDate
    fetchSchedules(midDate.getFullYear(), midDate.getMonth() + 1)
}

async function fetchSchedules(year, month) {
    loading.value = true
    try {
        const [schedulesRes, holidaysRes] = await Promise.all([
            request.get('/schedules/', { params: { year, month } }),
            request.get('/holidays/', { params: { year, month } })
        ])
        const hMap = {}; holidaysRes.forEach(h => { hMap[h.date] = h }); holidaysMap.value = hMap

        const techDutyMap = new Set()
        schedulesRes.forEach(item => { if (item.duty_type === '技术值班') techDutyMap.add(`${item.date}_${item.staff_name}`) })

        const events = []
        schedulesRes.forEach(item => {
            if (item.duty_type === '日间值班') {
                const key = `${item.date}_${item.staff_name}`; if (techDutyMap.has(key)) return 
            }
            const phoneStr = item.staff_phone ? ` ${item.staff_phone}` : ''
            const prefix = dutyLabelMap[item.duty_type] || `[${item.duty_type.substring(0,1)}]`
            events.push({
                title: `${prefix} ${item.staff_name}${phoneStr}`,
                start: item.date,
                color: dutyColorMap[item.duty_type] || '#555',
                extendedProps: {
                    rank: dutyRankMap[item.duty_type] || 99,
                    id: item.id, staff_name: item.staff_name, staff_phone: item.staff_phone, duty_type: item.duty_type
                }
            })
        })
        calendarEvents.value = events
    } catch (err) { } finally { loading.value = false }
}
</script>

<template>
  <div class="dashboard-container">
    <n-layout style="height: 100vh; background: transparent;">
      <n-layout-header class="nav-header">
        <div class="brand">
          <span class="logo-text">技术中心值班系统</span>
          <n-tag v-if="isAdmin" type="success" size="small" round bordered>管理模式</n-tag>
          <n-tag v-else type="default" size="small" round bordered>只读模式</n-tag>
        </div>
        <div class="nav-controls">
          <n-space align="center">
            <n-button strong secondary type="info" @click="router.push('/stats')">📊 数据分析</n-button>
            <n-button strong secondary type="warning" @click="router.push('/compensatory')">🛌 调休管理</n-button>
            <template v-if="isAdmin">
                <n-button strong secondary type="info" @click="openWeComSettings">🤖 企微通知设置</n-button>
                <n-button strong secondary type="error" @click="openHolidayManage">📅 节假日与保障期</n-button>
                <n-button v-if="currentUser.role === 'super_admin'" strong secondary type="success" @click="openUserManage">👥 账号管理</n-button>
                
                <n-button type="primary" ghost @click="openImportCenter">📂 数据导入/导出</n-button>
                
                <n-button size="small" type="error" ghost @click="handleLogout">退出登录</n-button>
            </template>
            <template v-else><n-button type="primary" @click="goToLogin">🔑 管理员登录</n-button></template>
          </n-space>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px; background: transparent; display: flex; flex-direction: column;">
        <n-spin :show="loading" description="加载中...">
            <n-card class="calendar-card" :bordered="false">
                <FullCalendar :options="calendarOptions" class="duty-calendar" />
            </n-card>
        </n-spin>

        <div class="app-footer">
            © {{ new Date().getFullYear() }} System developed by <span style="font-weight: bold">ZMW</span>. All rights reserved.
        </div>
      </n-layout-content>
    </n-layout> <template v-if="isAdmin">
      <n-modal 
            v-model:show="showWeComModal" 
            preset="card" 
            title="企业微信通知设置" 
            style="width: 500px"
            :bordered="false"
        >
            <n-form>
                <n-form-item label="Webhook 地址">
                    <n-input v-model:value="weComForm.webhook_url" placeholder="https://qyapi.weixin.qq.com/..." />
                </n-form-item>
                <n-form-item label="消息模板">
                    <n-input v-model:value="weComForm.message_template" type="textarea" :rows="5" placeholder="请填入模板内容..." />
                </n-form-item>
                <n-form-item label="每日自动发送时间 (留空则关闭)">
                    <n-time-picker v-model:formatted-value="weComForm.daily_time" format="HH:mm" value-format="HH:mm" placeholder="选择时间 (如 09:00)" style="width: 100%" clearable />
                </n-form-item>
                
                <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                    <n-button type="warning" ghost @click="testSendWeCom">📨 测试发送</n-button>
                    <div style="display: flex; gap: 10px;">
                        <n-button @click="closeWeComSettings">取消</n-button>
                        <n-button type="primary" @click="saveWeComSettings">保存配置</n-button>
                    </div>
                </div>
            </n-form>
        </n-modal>

        <n-modal v-model:show="showUserManageModal" preset="card" title="账号管理" style="width: 600px">
            <n-card :bordered="false" title="添加新管理员" size="small" style="margin-bottom: 20px;">
                <n-space vertical>
                    <n-input v-model:value="newUserForm.username" placeholder="登录账号" />
                    <n-input v-model:value="newUserForm.real_name" placeholder="真实姓名" />
                    <n-input v-model:value="newUserForm.password" type="password" placeholder="密码" />
                    <n-button type="primary" block @click="createUser">创建账号</n-button>
                </n-space>
            </n-card>
            <n-list bordered>
                <n-list-item v-for="u in userList" :key="u.id">
                    <n-thing :title="u.real_name" :description="u.role" />
                    <template #suffix><n-button v-if="u.role !== 'super_admin'" size="small" type="error" @click="deleteUser(u.id)">删除</n-button></template>
                </n-list-item>
            </n-list>
        </n-modal>

        <n-modal v-model:show="showHolidayModal" preset="card" title="节假日与保障期设置" style="width: 600px">
            <n-card :bordered="false" size="small" style="margin-bottom: 20px; background: #f9f9f9;">
                <n-space vertical>
                    <n-date-picker v-model:value="newHolidayForm.rangeDate" type="daterange" placeholder="选择日期范围" style="width: 100%" clearable />
                    
                    <n-divider dashed style="margin: 10px 0">基础设置 (休/班)</n-divider>
                    <n-space align="center">
                        <n-switch v-model:value="newHolidayForm.enableType">
                            <template #checked>修改类型</template>
                            <template #unchecked>不修改类型</template>
                        </n-switch>
                        <n-radio-group v-model:value="newHolidayForm.type" :disabled="!newHolidayForm.enableType">
                            <n-radio-button value="holiday" label="休 (法定)" />
                            <n-radio-button value="workday" label="班 (补班)" />
                            <n-radio-button :value="null" label="清除设置" />
                        </n-radio-group>
                    </n-space>
                    <n-input v-if="newHolidayForm.enableType && newHolidayForm.type" v-model:value="newHolidayForm.name" placeholder="节假日名称 (如: 春节)" />

                    <n-divider dashed style="margin: 10px 0">叠加设置 (保障期)</n-divider>
                    <n-space align="center">
                         <n-checkbox v-model:checked="newHolidayForm.enableGuarantee" size="large">
                            设为重要保障期
                         </n-checkbox>
                    </n-space>
                    <n-input v-if="newHolidayForm.enableGuarantee" v-model:value="newHolidayForm.guaranteeName" placeholder="保障期名称 (如: 两会保障)" />

                    <n-button type="primary" block @click="createHolidayBatch" style="margin-top: 10px">执行设置</n-button>
                </n-space>
            </n-card>
            <div style="max-height: 300px; overflow-y: auto;">
                <n-list bordered>
                    <n-list-item v-for="h in holidaysList" :key="h.id">
                        <n-space justify="space-between" align="center">
                            <div style="display: flex; gap: 5px; align-items: center;">
                                <span style="font-weight: bold; width: 90px;">{{ h.date }}</span>
                                <n-tag v-if="h.type === 'holiday'" type="error" size="small">休: {{ h.name }}</n-tag>
                                <n-tag v-if="h.type === 'workday'" type="default" size="small">班: {{ h.name }}</n-tag>
                                <n-tag v-if="h.is_guarantee" type="warning" size="small">保: {{ h.guarantee_name }}</n-tag>
                            </div>
                            <n-button size="small" type="error" ghost @click="deleteHoliday(h.id)">删除</n-button>
                        </n-space>
                    </n-list-item>
                </n-list>
            </div>
        </n-modal>

        <n-modal v-model:show="showEditModal" preset="card" title="调整排班" style="width: 400px">
            <n-form>
                <n-form-item label="值班人员"><n-input v-model:value="editForm.staff_name" /></n-form-item>
                <n-form-item label="联系电话"><n-input v-model:value="editForm.staff_phone" /></n-form-item>
                <n-form-item label="日期"><n-input type="date" v-model:value="editForm.date" /></n-form-item>
                <n-form-item label="岗位类型"><n-select v-model:value="editForm.duty_type" :options="dutyOptions" /></n-form-item>
                <n-space justify="end">
                    <n-button type="error" ghost @click="deleteSchedule">删除</n-button>
                    <n-button type="primary" @click="saveScheduleChange">保存修改</n-button>
                </n-space>
            </n-form>
        </n-modal>

        <n-modal v-model:show="showImportModal" preset="card" title="数据管理中心" style="width: 700px">
            <n-tabs type="line" animated>
                <n-tab-pane name="schedule" tab="📅 排班表导入">
                    <n-space vertical>
                        <n-card size="small" title="导入选项" embedded :bordered="false">
                             <n-space align="center">
                                <n-switch v-model:value="isOverwriteSchedule">
                                    <template #checked>覆盖模式 (推荐)</template>
                                    <template #unchecked>追加模式</template>
                                </n-switch>
                                <span style="font-size: 12px; color: #666;">
                                    {{ isOverwriteSchedule ? '检测Excel中的日期范围，先清空该范围内所有旧排班，再写入新数据。' : '直接追加数据，如果日期和人员相同可能会产生重复显示。' }}
                                </span>
                             </n-space>
                        </n-card>
                        
                        <n-upload directory-dnd :custom-request="customRequest" :data="{ type: 'schedule' }" :show-file-list="false" accept=".xlsx, .xls">
                            <n-upload-dragger>
                                <div style="margin-bottom: 12px"><n-icon size="48" :depth="3">📅</n-icon></div>
                                <n-text style="font-size: 16px">点击或拖拽排班表 Excel 到此处</n-text>
                                <n-p depth="3" style="margin: 8px 0 0 0">支持 .xlsx 文件，建议使用覆盖模式以避免数据重复。</n-p>
                            </n-upload-dragger>
                        </n-upload>
                    </n-space>
                </n-tab-pane>

                <n-tab-pane name="contact" tab="📒 通讯录导入">
                    <n-upload directory-dnd :custom-request="customRequest" :data="{ type: 'contact' }" :show-file-list="false" accept=".xlsx, .xls">
                        <n-upload-dragger>
                            <div style="margin-bottom: 12px"><n-icon size="48" :depth="3">👥</n-icon></div>
                            <n-text style="font-size: 16px">点击或拖拽通讯录 Excel 到此处</n-text>
                            <n-p depth="3" style="margin: 8px 0 0 0">系统将根据姓名自动更新部门和电话信息。</n-p>
                        </n-upload-dragger>
                    </n-upload>
                </n-tab-pane>

                <n-tab-pane name="history" tab="📜 导入历史">
                    <n-data-table :columns="historyColumns" :data="importHistory" :pagination="{ pageSize: 5 }" size="small" />
                </n-tab-pane>
            </n-tabs>
        </n-modal>
    </template>
  </div>
</template>
<style>
/* --- 1. 日历单元格头部布局系统 (保留 Flexbox 解决冲突) --- */
.day-cell-header {
    display: flex;
    justify-content: space-between; /* 左右推开 */
    align-items: flex-start;        /* 顶部对齐 */
    width: 100%;
    height: 100%;
    padding-top: 4px; /* 顶部留一点呼吸感 */
}

/* 左侧区域 (保障期) */
.header-left {
    display: flex;
    flex-direction: column; 
    align-items: flex-start;
    max-width: 45%; 
    padding-left: 4px; /* 左侧边距 */
}

/* 右侧区域 (日期 + 节假日) */
.header-right {
    display: flex;
    flex-direction: column; 
    align-items: flex-end;  
    flex: 1;
    padding-right: 8px; /* 右侧边距，还原原本日期的位置感 */
}

/* --- 2. 标签与字体还原 --- */

/* 通用标签文字还原 */
.tag-text {
    font-size: 12px; /* 还原大小 */
    font-weight: bold; /* 还原粗细 */
    white-space: nowrap; 
    overflow: hidden;
    text-overflow: ellipsis; 
    max-width: 100%;
    line-height: 1.2;
}

/* 通用标签图标还原 */
.tag-icon {
    display: inline-block;
    padding: 1px 4px; /* 还原内边距 */
    border-radius: 4px;
    font-size: 12px;  /* 还原大小 */
    font-weight: bold;
    line-height: 1;   /* 紧凑行高 */
    color: #fff;
    flex-shrink: 0;
}

/* --- 具体配色还原 --- */

/* 保障期 (左侧) - 紫色渐变 */
.guarantee-icon {
    background: linear-gradient(135deg, #6600cc 0%, #a855f7 100%);
    border: 1px solid #6600cc; /* 还原边框 */
    box-shadow: 0 2px 4px rgba(102, 0, 204, 0.3);
}
.guarantee-text {
    color: #6600cc;
    font-weight: 800; /* 还原超粗体 */
    margin-top: 2px;
}

/* 节假日 (右侧) - 红色 */
.holiday-group {
    display: flex;
    align-items: center;
    gap: 4px; /* 稍微拉开一点文字和图标的距离 */
    margin-bottom: 2px;
}
.holiday-icon {
    color: #d03050;
    background: rgba(208, 48, 80, 0.1);
    border: 1px solid rgba(208, 48, 80, 0.2);
}
.holiday-text {
    color: #d03050;
}

/* 工作日/补班 (右侧) - 灰色 */
.workday-icon {
    color: #666;
    background: #eee;
    border: 1px solid #ddd;
}
.workday-text {
    color: #666;
}

/* --- 日期数字还原 (重点) --- */
.day-number {
    font-family: 'Helvetica Neue', sans-serif; /* 还原原本的字体 */
    font-size: 18px; /* 还原原本的大小 */
    font-weight: 700; /* 还原原本的粗细 */
    color: #333;
    line-height: 1;
    text-decoration: none !important;
    margin-top: 4px; /* 与上方标签的距离 */
    position: relative;
    z-index: 2;
}
.fc-day-today .day-number {
    color: #2080f0; /* 今天的高亮色 */
    font-size: 20px;
}

/* --- 全局字体与框架样式还原 --- */
.dashboard-container { background-color: #f5f7fa; min-height: 100vh; color: #333; }
.nav-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; border-bottom: 1px solid #e1e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 20px; font-weight: 800; color: #2c3e50; letter-spacing: 0.5px; }
.calendar-card { background: #ffffff !important; border: 1px solid #ebeef5; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }

/* FullCalendar 基础字体还原 */
.fc { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
    color: #2c3e50; 
}
.fc-theme-standard td, .fc-theme-standard th { border-color: #e6e6e6; }
.fc-col-header-cell-cushion { color: #555; font-weight: 600; padding: 10px 0; }

/* 强制清除 FullCalendar 默认样式干扰，适配我们的 Flex 布局 */
.fc-daygrid-day-top {
    flex-direction: row; 
    display: block !important; 
}
.fc-daygrid-day-number {
    width: 100%;
    padding: 0 !important;
    text-decoration: none !important;
}


.app-footer {
    text-align: center;
    margin-top: 40px;      /* 离内容远一点 */
    margin-bottom: 20px;
    color: #999999;        /* 浅灰色，非常低调 */
    font-size: 12px;       /* 字体调小 */
    font-family: monospace; /* 看起来更像代码风格 */
    opacity: 0.6;          /* 降低透明度，不抢眼 */
}
.app-footer:hover {
    opacity: 1;            /* 鼠标放上去变清晰 */
    transition: opacity 0.3s;
}


/* 周末背景 */
.fc-day-sat, .fc-day-sun { background-color: #fcfcfc !important; }

/* 按钮与标题 */
.fc-toolbar-title { font-size: 24px !important; font-weight: 700; color: #2c3e50; }
.fc-button { background-color: #f5f5f5 !important; border-color: #d9d9d9 !important; color: #333 !important; font-weight: 600; }
.fc-button-active { background-color: #2080f0 !important; color: #fff !important; border-color: #2080f0 !important; }
/* 请替换或修改原有的 .fc-event 样式 */


.fc-event,
.fc-event * {  /* 重点：加上星号，强制作用于内部所有子元素 */
    cursor: text !important;
    user-select: text !important;
    -webkit-user-select: text !important;
}

.fc-event {
    border: none;
    margin-top: 2px;
    margin-bottom: 2px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer !important;
    /* === 新增代码开始：强制允许文本选中 === */
    user-select: none;
    -webkit-user-select: text !important;
    /* === 新增代码结束 === */
    /* 新增：稍微增加圆角，看起来更圆润 */
    border-radius: 6px; 
    
    /* 新增：左右增加一点内边距，文字不贴边 */
    padding: 2px 6px; 
    
    /* 新增：整体透明度 0.9，让背景色不那么“实”，稍微透一点底色，视觉更轻盈 */
    opacity: 0.9;
    
    /* 新增：微弱的阴影，增加层次感 */
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    
    /* 新增：过渡效果，让 hover 变色更丝滑 */
    transition: all 0.2s ease;
}
/* 添加一个点击时的按压效果，增加操作反馈 */
.fc-event:active {
    transform: scale(0.98);
    opacity: 1;
}

/* 新增：鼠标悬停时加深显示，方便确认当前选中的是哪一个 */
.fc-event:hover {
    opacity: 1;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    z-index: 10; /* 悬停时浮在最上层 */
}
</style>
