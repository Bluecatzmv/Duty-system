<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { 
    useMessage, NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NTag, 
    NCard, NGrid, NGridItem, NSelect, NList, NListItem, NThing, NModal, NForm, NFormItem, NRadioGroup, NRadio 
} from 'naive-ui'
import request from '../utils/request'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const router = useRouter()
const message = useMessage()

// 状态
const currentYear = ref(new Date().getFullYear())
const overviewList = ref([]) // 左侧人员
const selectedStaff = ref(null) // 当前选中人
const calendarEvents = ref([]) // 右侧日历事件
const quotaList = ref([]) // 可用额度列表 (用于弹窗选择)

// 弹窗状态
const showRedeemModal = ref(false)
const redeemForm = ref({
    redeemDate: '', // 点击日历获取的日期
    scheduleId: null // 选择消耗哪个额度
})

const yearOptions = [
    { label: '2024年', value: 2024 },
    { label: '2025年', value: 2025 },
    { label: '2026年', value: 2026 }
]

const calendarOptions = ref({
    plugins: [dayGridPlugin, interactionPlugin],
    initialView: 'dayGridMonth',
    locale: 'zh-cn',
    firstDay: 1,
    headerToolbar: { left: 'prev,next today', center: 'title', right: '' },
    events: calendarEvents,
    dateClick: handleDateClick, // 点击空白处：申请调休
    eventClick: handleEventClick // 点击事件：查看或撤销
})

onMounted(() => {
    fetchOverview()
})

const goBack = () => router.push('/')

// 1. 获取左侧列表
async function fetchOverview() {
    try {
        const res = await request.get('/compensatory/overview', { params: { year: currentYear.value } })
        overviewList.value = res
        if (res.length > 0 && !selectedStaff.value) {
            handleSelectStaff(res[0])
        } else if (selectedStaff.value) {
            const staff = res.find(i => i.name === selectedStaff.value.name)
            if (staff) selectedStaff.value = staff
            // 刷新右侧数据
            await fetchCalendarData(staff.name)
        }
    } catch (e) { message.error("数据加载失败") }
}

// 2. 选中某人
async function handleSelectStaff(staff) {
    selectedStaff.value = staff
    await fetchCalendarData(staff.name)
}

// 3. 获取日历数据
async function fetchCalendarData(name) {
    try {
        const res = await request.get(`/compensatory/calendar/${name}`, { params: { year: currentYear.value } })
        calendarEvents.value = res.events
        quotaList.value = res.quota_list
    } catch (e) { message.error("日历加载失败") }
}

// 4. 日历点击：申请调休
function handleDateClick(info) {
    // 检查是否已有额度
    if (quotaList.value.length === 0) {
        message.warning("当前没有可用的调休额度")
        return
    }
    
    redeemForm.value = {
        redeemDate: info.dateStr,
        scheduleId: quotaList.value[0].id // 默认选最早的一个
    }
    showRedeemModal.value = true
}

// 5. 事件点击：撤销
async function handleEventClick(info) {
    const props = info.event.extendedProps
    if (props.type === 'leave') {
        if (!window.confirm(`确定要撤销 ${info.event.startStr} 的调休记录吗？额度将返还。`)) return
        
        try {
            await request.delete(`/compensatory/redeem/${props.redemption_id}`)
            message.success("已撤销")
            await fetchOverview() // 刷新左侧余额
            await fetchCalendarData(selectedStaff.value.name) // 刷新右侧日历
        } catch (e) { message.error("撤销失败") }
    }
}

// 6. 提交调休
async function submitRedeem() {
    if (!redeemForm.value.scheduleId) return message.warning("请选择消耗哪个额度")
    
    try {
        await request.post('/compensatory/redeem', {
            staff_name: selectedStaff.value.name,
            redeem_date: redeemForm.value.redeemDate,
            schedule_id: redeemForm.value.scheduleId
        })
        message.success("登记成功")
        showRedeemModal.value = false
        await fetchOverview()
        await fetchCalendarData(selectedStaff.value.name)
    } catch (e) {
        message.error("操作失败：" + (e.response?.data?.detail || "未知错误"))
    }
}
</script>

<template>
  <div class="comp-container">
    <n-layout style="height: 100vh; background: transparent;">
      <n-layout-header class="nav-header">
        <div class="brand">
          <span class="logo-text">调休管理系统</span>
          <n-tag type="warning" size="small" round bordered>1值班=2调休</n-tag>
        </div>
        <div class="nav-controls">
            <n-space align="center">
                <span>统计年份：</span>
                <n-select v-model:value="currentYear" :options="yearOptions" style="width: 100px" @update:value="fetchOverview" />
                <n-button type="primary" ghost @click="goBack">返回主页</n-button>
            </n-space>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px; background: transparent;">
        <n-grid x-gap="24" :cols="3" style="height: calc(100vh - 100px);">
            
            <n-grid-item :span="1">
                <n-card title="人员调休余额表" :bordered="false" class="shadow-card" style="height: 100%; display: flex; flex-direction: column;">
                    <div style="overflow-y: auto; flex: 1; padding-right: 4px;">
                        <n-list hoverable clickable>
                            <n-list-item v-for="item in overviewList" :key="item.name" @click="handleSelectStaff(item)"
                                :class="{ 'active-item': selectedStaff && selectedStaff.name === item.name }">
                                <n-thing>
                                    <template #header>{{ item.name }}</template>
                                    <template #header-extra>
                                        <n-tag :type="item.balance > 0 ? 'error' : 'success'" round>
                                            待休: {{ item.balance }} 天
                                        </n-tag>
                                    </template>
                                    <template #description>
                                        <span style="font-size: 12px; color: #999;">
                                            累计产生: {{ item.total_earned_days }}天 | 已休: {{ item.total_redeemed_days }}天
                                        </span>
                                    </template>
                                </n-thing>
                            </n-list-item>
                        </n-list>
                    </div>
                </n-card>
            </n-grid-item>
            
            <n-grid-item :span="2">
                <n-card v-if="selectedStaff" :bordered="false" class="shadow-card" style="height: 100%;">
                    <template #header>
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span>{{ selectedStaff.name }} 的调休台账</span>
                            <div style="font-size: 14px; font-weight: normal; color: #666;">
                                点击空白日期登记调休，点击绿色条撤销
                            </div>
                        </div>
                    </template>
                    
                    <FullCalendar :options="calendarOptions" style="height: 100%;" />
                </n-card>
            </n-grid-item>
        </n-grid>
      </n-layout-content>
    </n-layout>
    
    <n-modal v-model:show="showRedeemModal" preset="card" title="登记调休" style="width: 450px">
        <p>你选择在 <span style="color: #2080f0; font-weight: bold;">{{ redeemForm.redeemDate }}</span> 调休 1 天</p>
        <p style="margin-bottom: 10px; color: #666;">请选择消耗哪一次值班产生的额度：</p>
        
        <n-form>
            <n-form-item>
                <n-radio-group v-model:value="redeemForm.scheduleId" name="quotaGroup">
                    <n-space vertical>
                        <n-radio v-for="q in quotaList" :key="q.id" :value="q.id">
                            {{ q.date }} 值班 (剩余 {{ q.remaining }} 天)
                        </n-radio>
                    </n-space>
                </n-radio-group>
            </n-form-item>
            
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
                <n-button @click="showRedeemModal = false">取消</n-button>
                <n-button type="primary" @click="submitRedeem">确认登记</n-button>
            </div>
        </n-form>
    </n-modal>
  </div>
</template>

<style scoped>
.comp-container { background-color: #f5f7fa; min-height: 100vh; color: #333; }
.nav-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; border-bottom: 1px solid #e1e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo-text { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 20px; font-weight: 800; color: #2c3e50; }
.shadow-card { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.active-item { background-color: #f0f7ff; border-right: 3px solid #2080f0; }

/* 调整日历样式 */
:deep(.fc-event) {
    cursor: pointer;
    font-size: 12px;
}
:deep(.fc-daygrid-day) {
    cursor: pointer;
}
:deep(.fc-daygrid-day:hover) {
    background-color: #f9f9f9;
}
</style>
