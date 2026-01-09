<script setup>
import { ref, onMounted, computed } from 'vue' 
import { useRouter } from 'vue-router'
import { 
    useMessage, NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NTag, 
    NCard, NSpin, NModal, NForm, NFormItem, NInput, NSelect, NList, NListItem, 
    NThing, NDatePicker, NRadioGroup, NRadio, NTimePicker, NRadioButton, 
    NDivider, NSwitch, NCheckbox, NTabs, NTabPane, NUpload, NUploadDragger, 
    NIcon, NDataTable, NText, NP, NAlert
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

// === 新增：修改密码相关状态 ===
const showPasswordModal = ref(false)
const passwordForm = ref({ userId: null, realName: '', newPassword: '' })

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

// 数据导入中心状态
const showImportModal = ref(false)
const importHistory = ref([])
const isOverwriteSchedule = ref(true) 
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
    '总值班': '#ef7a7a', '技术值班': '#6aa1e6', '日间值班': '#6bc495', 
    '夜间值班': '#f2b05e', '夜间见习': '#a68cd6', '更新值班': '#5dc5d6', '更新见习': '#a8a8a8'
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
    initialView: 'dayGridMonth',
    locale: 'zh-cn',
    firstDay: 1,
    headerToolbar: { left: 'prev,next today', center: 'title', right: '' },
    eventDisplay: 'block', events: calendarEvents,
    eventOrder: 'rank', datesSet: handleDatesSet, 
    
    // 点击逻辑（包含复制功能）
    eventClick: handleEventClick,
    
    // 渲染自定义 HTML
    dayCellContent: (arg) => {
        const dateStr = formatDateLocal(arg.date)
        const holiday = holidaysMap.value[dateStr]
        const dayNumber = arg.dayNumberText
        let html = `<div class="day-cell-header">`
        html += `<div class="header-left">`
        if (holiday && holiday.is_guarantee) {
            const gName = holiday.guarantee_name || ''
            html += `<span class="tag-icon guarantee-icon">保</span>`
            if (gName) html += `<span class="tag-text guarantee-text">${gName}</span>`
        }
        html += `</div>`
        html += `<div class="header-right">`
        if (holiday) {
            if (holiday.type === 'holiday') {
                html += `<div class="holiday-group"><span class="tag-text holiday-text">${holiday.name || ''}</span><span class="tag-icon holiday-icon">休</span></div>`
            } else if (holiday.type === 'workday') {
                html += `<div class="holiday-group"><span class="tag-text workday-text">${holiday.name || ''}</span><span class="tag-icon workday-icon">班</span></div>`
            }
        }
        html += `<span class="day-number">${dayNumber}</span></div></div>`
        return { html: html }
    },
    
    // 强制允许文本选择（防止拖拽干扰）
    eventDidMount: function(info) {
        info.el.style.userSelect = 'text';
        info.el.setAttribute('draggable', 'false');
        info.el.onmousedown = (e) => { e.stopPropagation(); };
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

// 核心：点击事件（管理员编辑，普通用户复制）
function handleEventClick(info) {
    const props = info.event.extendedProps
    const staffName = props.staff_name
    const staffPhone = props.staff_phone || ''
    const copyText = `${staffName} ${staffPhone}`.trim()

    // 1. 普通用户：执行复制
    if (!isAdmin.value) { 
        const copyToClipboard = (text) => {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            }
            return new Promise((resolve, reject) => {
                try {
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed"; textArea.style.left = "-9999px"; textArea.style.top = "0";
                    document.body.appendChild(textArea);
                    textArea.focus(); textArea.select();
                    const successful = document.execCommand('copy');
                    document.body.removeChild(textArea);
                    if (successful) resolve(); else reject(new Error("浏览器拒绝复制"));
                } catch (err) { reject(err); }
            });
        };
        copyToClipboard(copyText)
            .then(() => { message.success(`已复制: ${copyText}`) })
            .catch(() => { message.warning(`无法自动复制，请手动记录: ${copyText}`) });
        return; 
    }
    
    // 2. 管理员：弹出编辑框
    editForm.value = {
        id: props.id, staff_name: staffName, staff_phone: staffPhone,
        date: info.event.startStr, duty_type: props.duty_type
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

// === 新增：打开修改密码弹窗 ===
function openPasswordModal(user) {
    passwordForm.value = {
        userId: user.id,
        realName: user.real_name,
        newPassword: ''
    }
    showPasswordModal.value = true
}

// === 新增：提交修改密码 ===
async function submitPasswordChange() {
    if (!passwordForm.value.newPassword) return message.warning("请输入新密码")
    try {
        await request.put(`/users/${passwordForm.value.userId}/password`, {
            password: passwordForm.value.newPassword
        })
        message.success("密码修改成功")
        showPasswordModal.value = false
    } catch (e) {
        message.error("修改失败: " + (e.response?.data?.detail || "未知错误"))
    }
}

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
        start_date: fmt(startTs), end_date: fmt(endTs),
        update_type: newHolidayForm.value.enableType,
        type: newHolidayForm.value.enableType ? newHolidayForm.value.type : null,
        name: newHolidayForm.value.enableType ? newHolidayForm.value.name : null,
        update_guarantee: true,
        is_guarantee: newHolidayForm.value.enableGuarantee,
        guarantee_name: newHolidayForm.value.enableGuarantee ? newHolidayForm.value.guaranteeName : null
    }
    try {
        await request.post('/holidays/batch', payload); message.success("设置成功")
        const year = currentViewDate.value.getFullYear(); const month = currentViewDate.value.getMonth() + 1
        holidaysList.value = await request.get('/holidays/', { params: {year, month} }); fetchSchedules(year, month)
    } catch (e) { message.error("设置失败: " + e.message) }
}

async function deleteHoliday(id) {
    if (!window.confirm("确定要删除这个设置吗？")) return
    try { 
        loading.value = true; await request.delete(`/holidays/${id}`); message.success("已删除")
        const year = currentViewDate.value.getFullYear(); const month = currentViewDate.value.getMonth() + 1
        holidaysList.value = await request.get('/holidays/', { params: {year, month} }); fetchSchedules(year, month)
    } catch (e) { message.error("删除失败") } finally { loading.value = false }
}

// ================== 企微配置 ==================
async function openWeComSettings() {
    showWeComModal.value = true
    try { 
        const res = await request.get('/config/wecom')
        if (!res.daily_time) res.daily_time = null
        weComForm.value = res 
    } catch (e) { message.error("获取配置失败") }
}
async function saveWeComSettings() {
    try { await request.post('/config/wecom', weComForm.value); message.success("保存成功"); showWeComModal.value = false } catch (e) { message.error("保存失败") }
}
function closeWeComSettings() { showWeComModal.value = false }
async function testSendWeCom() {
    try { const res = await request.post('/notify/send'); if (res.status === 'success') message.success("发送成功"); else message.error(res.message) } catch (e) { message.error("发送失败") }
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

// ================== 数据导入/导出 ==================
async function openImportCenter() { showImportModal.value = true; await fetchImportHistory() }
async function fetchImportHistory() { try { importHistory.value = await request.get('/imports/history') } catch(e) {} }
async function handleUpload({ file, data }) {
    const formData = new FormData(); formData.append('file', file.file)
    if (data && data.type === 'schedule') formData.append('is_overwrite', isOverwriteSchedule.value)
    const url = data.type === 'schedule' ? '/schedules/import_excel' : '/contacts/import'
    uploadLoading.value = true
    try {
        const res = await request.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        message.success(res.msg); fetchSchedules(currentViewDate.value.getFullYear(), currentViewDate.value.getMonth() + 1); fetchImportHistory()
    } catch (e) { message.error("导入失败: " + (e.response?.data?.detail || e.message)) } finally { uploadLoading.value = false }
}
const customRequest = ({ file, data, onFinish, onError }) => { handleUpload({ file, data }).then(onFinish).catch(onError) }

// ================== 日历逻辑 ==================
function handleDatesSet(arg) {
    const midDate = new Date(arg.start.getTime() + (arg.end.getTime() - arg.start.getTime()) / 2)
    currentViewDate.value = midDate; fetchSchedules(midDate.getFullYear(), midDate.getMonth() + 1)
}
async function fetchSchedules(year, month) {
    loading.value = true
    try {
        const [schedulesRes, holidaysRes] = await Promise.all([
            request.get('/schedules/', { params: { year, month } }),
            request.get('/holidays/', { params: { year, month } })
        ])
        const hMap = {}; holidaysRes.forEach(h => { hMap[h.date] = h }); holidaysMap.value = hMap
        const techDutyMap = new Set(); schedulesRes.forEach(item => { if (item.duty_type === '技术值班') techDutyMap.add(`${item.date}_${item.staff_name}`) })
        const events = []
        schedulesRes.forEach(item => {
            if (item.duty_type === '日间值班') { const key = `${item.date}_${item.staff_name}`; if (techDutyMap.has(key)) return }
            const phoneStr = item.staff_phone ? ` ${item.staff_phone}` : ''
            const prefix = dutyLabelMap[item.duty_type] || `[${item.duty_type.substring(0,1)}]`
            events.push({
                title: `${prefix} ${item.staff_name}${phoneStr}`, start: item.date, color: dutyColorMap[item.duty_type] || '#555',
                extendedProps: { rank: dutyRankMap[item.duty_type] || 99, id: item.id, staff_name: item.staff_name, staff_phone: item.staff_phone, duty_type: item.duty_type }
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
            <n-button strong secondary type="primary" @click="router.push('/contacts')">📒 通讯录</n-button>
            
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
        <div class="app-footer">© {{ new Date().getFullYear() }} System developed by <span style="font-weight: bold">ZMW</span>. All rights reserved.</div>
      </n-layout-content>
    </n-layout>

    <template v-if="isAdmin">
        <n-modal v-model:show="showWeComModal" preset="card" title="企业微信通知设置" style="width: 500px" :bordered="false">
            <n-form>
                <n-form-item label="Webhook 地址"><n-input v-model:value="weComForm.webhook_url" placeholder="https://qyapi.weixin.qq.com/..." /></n-form-item>
                <n-form-item label="消息模板"><n-input v-model:value="weComForm.message_template" type="textarea" :rows="5" placeholder="请填入模板内容..." /></n-form-item>
                <n-form-item label="每日自动发送时间 (留空则关闭)">
                    <n-time-picker v-model:formatted-value="weComForm.daily_time" format="HH:mm" value-format="HH:mm" placeholder="选择时间" style="width: 100%" clearable />
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
                    <n-thing :title="u.real_name" :description="u.username + ' (' + u.role + ')'" />
                    <template #suffix>
                        <n-space>
                            <n-button size="small" type="warning" ghost @click="openPasswordModal(u)">改密</n-button>
                            <n-button v-if="u.role !== 'super_admin'" size="small" type="error" @click="deleteUser(u.id)">删除</n-button>
                        </n-space>
                    </template>
                </n-list-item>
            </n-list>
        </n-modal>

        <n-modal v-model:show="showPasswordModal" preset="card" title="修改密码" style="width: 400px">
            <n-space vertical>
                <n-alert type="info" :show-icon="false">正在修改用户 <b>{{ passwordForm.realName }}</b> 的密码</n-alert>
                <n-input v-model:value="passwordForm.newPassword" type="password" show-password-on="click" placeholder="请输入新密码" />
                <n-space justify="end" style="margin-top: 10px">
                    <n-button @click="showPasswordModal = false">取消</n-button>
                    <n-button type="primary" @click="submitPasswordChange">确认修改</n-button>
                </n-space>
            </n-space>
        </n-modal>

        <n-modal v-model:show="showHolidayModal" preset="card" title="节假日与保障期设置" style="width: 600px">
            <n-card :bordered="false" size="small" style="margin-bottom: 20px; background: #f9f9f9;">
                <n-space vertical>
                    <n-date-picker v-model:value="newHolidayForm.rangeDate" type="daterange" placeholder="选择日期范围" style="width: 100%" clearable />
                    <n-divider dashed style="margin: 10px 0">基础设置</n-divider>
                    <n-space align="center">
                        <n-switch v-model:value="newHolidayForm.enableType"><template #checked>修改类型</template><template #unchecked>不修改类型</template></n-switch>
                        <n-radio-group v-model:value="newHolidayForm.type" :disabled="!newHolidayForm.enableType">
                            <n-radio-button value="holiday" label="休 (法定)" /><n-radio-button value="workday" label="班 (补班)" /><n-radio-button :value="null" label="清除设置" />
                        </n-radio-group>
                    </n-space>
                    <n-input v-if="newHolidayForm.enableType && newHolidayForm.type" v-model:value="newHolidayForm.name" placeholder="节假日名称" />
                    <n-divider dashed style="margin: 10px 0">保障期</n-divider>
                    <n-checkbox v-model:checked="newHolidayForm.enableGuarantee" size="large">设为重要保障期</n-checkbox>
                    <n-input v-if="newHolidayForm.enableGuarantee" v-model:value="newHolidayForm.guaranteeName" placeholder="保障期名称" />
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
                                <n-switch v-model:value="isOverwriteSchedule"><template #checked>覆盖模式</template><template #unchecked>追加模式</template></n-switch>
                                <span style="font-size: 12px; color: #666;">{{ isOverwriteSchedule ? '先清空该范围内所有旧排班' : '直接追加数据' }}</span>
                             </n-space>
                        </n-card>
                        <n-upload directory-dnd :custom-request="customRequest" :data="{ type: 'schedule' }" :show-file-list="false" accept=".xlsx, .xls">
                            <n-upload-dragger><div style="margin-bottom: 12px"><n-icon size="48" :depth="3">📅</n-icon></div><n-text style="font-size: 16px">点击或拖拽排班表 Excel</n-text></n-upload-dragger>
                        </n-upload>
                    </n-space>
                </n-tab-pane>
                <n-tab-pane name="contact" tab="📒 通讯录导入">
                    <n-upload directory-dnd :custom-request="customRequest" :data="{ type: 'contact' }" :show-file-list="false" accept=".xlsx, .xls">
                        <n-upload-dragger><div style="margin-bottom: 12px"><n-icon size="48" :depth="3">👥</n-icon></div><n-text style="font-size: 16px">点击或拖拽通讯录 Excel</n-text></n-upload-dragger>
                    </n-upload>
                </n-tab-pane>
                <n-tab-pane name="history" tab="📜 导入历史"><n-data-table :columns="historyColumns" :data="importHistory" :pagination="{ pageSize: 5 }" size="small" /></n-tab-pane>
            </n-tabs>
        </n-modal>
    </template>
  </div>
</template>

<style>
.day-cell-header { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; height: 100%; padding-top: 4px; }
.header-left { display: flex; flex-direction: column; align-items: flex-start; max-width: 45%; padding-left: 4px; }
.header-right { display: flex; flex-direction: column; align-items: flex-end; flex: 1; padding-right: 8px; }
.tag-text { font-size: 12px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; line-height: 1.2; }
.tag-icon { display: inline-block; padding: 1px 4px; border-radius: 4px; font-size: 12px; font-weight: bold; line-height: 1; color: #fff; flex-shrink: 0; }
.guarantee-icon { background: linear-gradient(135deg, #6600cc 0%, #a855f7 100%); border: 1px solid #6600cc; box-shadow: 0 2px 4px rgba(102, 0, 204, 0.3); }
.guarantee-text { color: #6600cc; font-weight: 800; margin-top: 2px; }
.holiday-group { display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }
.holiday-icon { color: #d03050; background: rgba(208, 48, 80, 0.1); border: 1px solid rgba(208, 48, 80, 0.2); }
.holiday-text { color: #d03050; }
.workday-icon { color: #666; background: #eee; border: 1px solid #ddd; }
.workday-text { color: #666; }
.day-number { font-family: 'Helvetica Neue', sans-serif; font-size: 18px; font-weight: 700; color: #333; line-height: 1; text-decoration: none !important; margin-top: 4px; position: relative; z-index: 2; }
.fc-day-today .day-number { color: #2080f0; font-size: 20px; }
.dashboard-container { background-color: #f5f7fa; min-height: 100vh; color: #333; }
.nav-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; border-bottom: 1px solid #e1e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 20px; font-weight: 800; color: #2c3e50; letter-spacing: 0.5px; }
.calendar-card { background: #ffffff !important; border: 1px solid #ebeef5; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.fc { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #2c3e50; }
.fc-theme-standard td, .fc-theme-standard th { border-color: #e6e6e6; }
.fc-col-header-cell-cushion { color: #555; font-weight: 600; padding: 10px 0; }
.fc-daygrid-day-top { flex-direction: row; display: block !important; }
.fc-daygrid-day-number { width: 100%; padding: 0 !important; text-decoration: none !important; }
.app-footer { text-align: center; margin-top: 40px; margin-bottom: 20px; color: #999999; font-size: 12px; font-family: monospace; opacity: 0.6; }
.app-footer:hover { opacity: 1; transition: opacity 0.3s; }
.fc-day-sat, .fc-day-sun { background-color: #fcfcfc !important; }
.fc-toolbar-title { font-size: 24px !important; font-weight: 700; color: #2c3e50; }
.fc-button { background-color: #f5f5f5 !important; border-color: #d9d9d9 !important; color: #333 !important; font-weight: 600; }
.fc-button-active { background-color: #2080f0 !important; color: #fff !important; border-color: #2080f0 !important; }
.fc-event { border: none; margin-top: 2px; margin-bottom: 2px; font-size: 12px; font-weight: 500; cursor: pointer !important; user-select: text !important; -webkit-user-select: text !important; border-radius: 6px; padding: 2px 6px; opacity: 0.9; box-shadow: 0 1px 3px rgba(0,0,0,0.08); transition: all 0.2s ease; }
.fc-event:active { transform: scale(0.98); opacity: 1; }
.fc-event:hover { opacity: 1; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); z-index: 10; }
.fc-event * { cursor: pointer !important; user-select: text !important; -webkit-user-select: text !important; }
</style>
