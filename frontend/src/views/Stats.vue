<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
    NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NCard, NGrid, NGridItem, 
    NSelect, NStatistic, NNumberAnimation, NEmpty, NTag, NTabs, NTabPane, NSpin
} from 'naive-ui'
import request from '../utils/request'
import * as echarts from 'echarts'

const router = useRouter()
const currentYear = ref(new Date().getFullYear())
const loading = ref(false)

// --- 部门筛选相关 ---
const currentDept = ref(null)
const deptOptions = ref([])

// --- 数据源 ---
const allStats = ref([]) 
const advancedStats = ref({ weekday_stats: [], holiday_stats: { groups: [] } })
const selectedStaff = ref(null) 
const currentTab = ref('overview') 

// --- 图表实例 ---
let chartRank = null
let chartPie = null 
let chartLine = null

const yearOptions = [
    { label: '2024年', value: 2024 },
    { label: '2025年', value: 2025 },
    { label: '2026年', value: 2026 },
    { label: '2027年', value: 2027 }
]

// --- Computed: 年度日历 ---
const monthlyDetailsList = computed(() => {
    const list = []
    for (let i = 1; i <= 12; i++) list.push({ month: i, details: [] })
    if (!selectedStaff.value || !selectedStaff.value.details) return list
    selectedStaff.value.details.forEach(item => {
        const dateObj = new Date(item.date)
        const m = dateObj.getMonth() 
        const day = dateObj.getDate()
        const typeShort = item.type.substring(0, 1)
        list[m].details.push({
            day: day,
            fullDate: item.date,
            type: item.type,
            typeShort: typeShort,
            isHoliday: item.is_holiday,
            isWeekend: item.is_weekend
        })
    })
    return list
})

// --- Computed: 周番矩阵 ---
const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const maxMatrixValue = computed(() => {
    let max = 0
    if (advancedStats.value && advancedStats.value.weekday_stats) {
        advancedStats.value.weekday_stats.forEach(p => {
            p.counts.forEach(c => { if(c > max) max = c })
        })
    }
    return max || 1
})

onMounted(async () => {
    await initDeptOptions() // 1. 先初始化部门
    window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeCharts)
    disposeCharts()
})

// 监听部门和年份变化，重新获取数据
watch([currentYear, currentDept], () => {
    if (currentDept.value) {
        fetchData()
    }
})

// 监听 Tab 切换，解决 ECharts 在 v-if 中不显示的问题
watch(currentTab, (newVal) => {
    if (newVal === 'overview') {
        nextTick(() => {
            setTimeout(() => {
                initRankChart()
                updateDetailCharts()
            }, 50)
        })
    }
})

function disposeCharts() {
    if (chartRank) { chartRank.dispose(); chartRank = null }
    if (chartPie) { chartPie.dispose(); chartPie = null }
    if (chartLine) { chartLine.dispose(); chartLine = null }
}

const resizeCharts = () => {
    chartRank?.resize()
    chartPie?.resize()
    chartLine?.resize()
}

const goBack = () => router.push('/')

// 初始化部门选项
async function initDeptOptions() {
    try {
        const contacts = await request.get('/contacts/public')
        // 提取去重后的部门列表
        const depts = new Set()
        contacts.forEach(c => {
            if (c.department) depts.add(c.department)
        })
        
        const opts = [{ label: '全部部门', value: '全部' }]
        depts.forEach(d => opts.push({ label: d, value: d }))
        deptOptions.value = opts
        
        // 默认逻辑：如果有“技术中心”，优先选它，否则选“全部”
        if (depts.has('技术中心')) {
            currentDept.value = '技术中心'
        } else {
            currentDept.value = '全部'
        }
        
        // 触发第一次数据加载
        fetchData()
        
    } catch (e) {
        console.error("获取部门失败", e)
        // 降级处理
        deptOptions.value = [{ label: '全部部门', value: '全部' }]
        currentDept.value = '全部'
        fetchData()
    }
}

async function fetchData() {
    if (!currentDept.value) return
    loading.value = true
    selectedStaff.value = null // 切换查询条件时重置选中人
    
    try {
        const params = { year: currentYear.value, department: currentDept.value }
        
        const [res, advRes] = await Promise.all([
            request.get('/stats/yearly', { params }),
            request.get('/stats/advanced', { params })
        ])
        
        allStats.value = res
        advancedStats.value = advRes
        
        if (res && res.length > 0) {
            // 默认选中第一个人
            selectedStaff.value = res[0]
            if (currentTab.value === 'overview') {
                nextTick(() => {
                    initRankChart()
                    updateDetailCharts()
                })
            }
        } else {
            // 如果没数据，清空图表
            disposeCharts()
        }
    } catch (e) { 
        console.error(e) 
    } finally {
        loading.value = false
    }
}

function initRankChart() {
    const dom = document.getElementById('chart-rank')
    // 增加判空逻辑，防止切换太快dom还没生成
    if (!dom || !allStats.value || allStats.value.length === 0) return 
    
    if (echarts.getInstanceByDom(dom)) {
        echarts.getInstanceByDom(dom).dispose()
    }
    
    chartRank = echarts.init(dom)
    
    // 使用全部数据，并进行反转，让第一名显示在最上面
    const sortedData = [...allStats.value]
    const names = sortedData.map(i => i.name)
    const totals = sortedData.map(i => i.total)

    const option = {
        title: { text: `年度值班排行榜 (${currentDept.value})`, left: 'center' },
        tooltip: { 
            trigger: 'axis', 
            axisPointer: { type: 'shadow' },
            confine: true // 防止提示框超出屏幕
        },
        // 【修改点 1】增加 right 的值，给右侧腾出更多空间
        // containLabel: true 会自动计算标签宽度，但有时候不够准确，手动增加 right 更稳妥
        grid: { left: '3%', right: '15%', bottom: '3%', top: '10%', containLabel: true },
        xAxis: { 
            type: 'value',
            minInterval: 1 // 保证刻度是整数
        },
        yAxis: { 
            type: 'category', 
            data: names,
            inverse: true, // 反转 Y 轴，让第一名显示在最顶部
            axisLabel: {
                interval: 0 // 强制显示所有名字
            }
        },
        // DataZoom 滚动条配置
        dataZoom: [
            {
                type: 'slider',
                yAxisIndex: 0,
                width: 20,       // 滚动条宽度
                // 【修改点 2】调整滑动条距离右侧容器边缘的距离
                right: 5,        // 让滑动条更靠右
                startValue: 0,   // 默认显示从第 0 个
                endValue: 14,    // 默认显示到第 14 个 (即一次显示15人)
                handleSize: '80%',
                brushSelect: false,
                zoomLock: false,
                showDetail: false // 不显示详细文字
            },
            {
                type: 'inside',   // 允许鼠标滚轮滚动
                yAxisIndex: 0,
                startValue: 0,
                endValue: 14,
                zoomOnMouseWheel: false,
                moveOnMouseWheel: true,
                moveOnMouseMove: true
            }
        ],
        series: [{
            name: '总天数', 
            type: 'bar', 
            data: totals,
            itemStyle: { color: '#5470c6' },
            label: { show: true, position: 'right' },
            barMaxWidth: 30 // 限制柱子最大宽度
        }]
    }
    chartRank.setOption(option)
    
    chartRank.on('click', (params) => {
        const name = params.name
        const staff = allStats.value.find(i => i.name === name)
        if (staff) {
            selectedStaff.value = staff
            updateDetailCharts()
        }
    })
}
function updateDetailCharts() {
    if (!selectedStaff.value) return
    const staff = selectedStaff.value
    
    // --- 饼图 ---
    const domPie = document.getElementById('chart-pie')
    if (domPie) {
        if (echarts.getInstanceByDom(domPie)) {
             echarts.getInstanceByDom(domPie).dispose()
        }
        chartPie = echarts.init(domPie)
        const pieData = [
            { value: staff.weekday_count, name: '工作日', itemStyle: { color: '#91cc75' } },
            { value: staff.weekend_count, name: '周末', itemStyle: { color: '#fac858' } },
            { value: staff.holiday_count, name: '法定节假日', itemStyle: { color: '#ee6666' } }
        ].filter(i => i.value > 0)
        
        chartPie.setOption({
            title: { 
                text: `${staff.name} - 值班类型`, 
                left: 'center',
                top: '2%' 
            },
            tooltip: { trigger: 'item' },
            legend: { top: 'bottom' },
            series: [{
                name: '类型', 
                type: 'pie', 
                radius: ['35%', '60%'], 
                center: ['50%', '55%'], 
                avoidLabelOverlap: false,
                itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
                data: pieData
            }]
        })
    }
    
    // --- 折线图 ---
    const domLine = document.getElementById('chart-line')
    if (domLine) {
        if (echarts.getInstanceByDom(domLine)) {
             echarts.getInstanceByDom(domLine).dispose()
        }
        chartLine = echarts.init(domLine)
        chartLine.setOption({
            title: { text: '月度趋势', left: 'center', top: '2%' },
            tooltip: { trigger: 'axis' },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: { type: 'category', data: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'] },
            yAxis: { type: 'value', minInterval: 1 },
            series: [{
                data: staff.months, type: 'line', smooth: true,
                areaStyle: { opacity: 0.3 }, itemStyle: { color: '#5470c6' }
            }]
        })
    }
}

function getHeatmapStyle(count) {
    if (count === 0) return { background: '#f5f7fa', color: '#ccc' }
    const alpha = Math.min(count / maxMatrixValue.value + 0.1, 1)
    return {
        background: `rgba(32, 128, 240, ${alpha})`,
        color: alpha > 0.6 ? '#fff' : '#333',
        fontWeight: 'bold'
    }
}
</script>

<template>
  <div class="stats-container">
    <n-layout style="height: 100vh; background: transparent;">
      <n-layout-header class="nav-header">
        <div class="brand">
          <span class="logo-text">数据分析中心</span>
          <n-tag type="info" size="small" round bordered>STATISTICS</n-tag>
        </div>
        <div class="nav-controls">
            <n-space align="center">
                <span style="color: #666;">年份：</span>
                <n-select v-model:value="currentYear" :options="yearOptions" style="width: 100px" />
                
                <span style="color: #666; margin-left: 10px;">部门：</span>
                <n-select 
                    v-model:value="currentDept" 
                    :options="deptOptions" 
                    placeholder="选择部门" 
                    style="width: 140px" 
                />

                <n-button type="primary" ghost @click="goBack" style="margin-left: 10px;">返回排班表</n-button>
            </n-space>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px; background: transparent;">
        <n-spin :show="loading">
            <div v-if="!loading && (!allStats || allStats.length === 0)" style="margin-top: 100px;">
                <n-empty :description="currentDept + ' 在 ' + currentYear + ' 年暂无值班数据'">
                    <template #extra><n-button size="small" @click="goBack">去完善数据</n-button></template>
                </n-empty>
            </div>

            <n-tabs v-else v-model:value="currentTab" type="line" animated>
                <n-tab-pane name="overview" tab="📊 年度概览">
                    <n-grid x-gap="24" y-gap="24" :cols="3">
                        <n-grid-item :span="1">
                            <n-card :title="'🏆 年度值班总览 (' + currentDept + ')'" :bordered="false" class="shadow-card">
                                <div id="chart-rank" style="width: 100%; height: 600px;"></div>
                            </n-card>
                        </n-grid-item>
                        
                        <n-grid-item :span="2">
                            <n-space vertical size="large">
                                <n-card v-if="selectedStaff" :bordered="false" class="info-card shadow-card">
                                    <n-grid :cols="4">
                                        <n-grid-item>
                                            <n-statistic label="当前查看">
                                                <span style="font-weight: bold; color: #2080f0; font-size: 24px;">{{ selectedStaff.name }}</span>
                                            </n-statistic>
                                        </n-grid-item>
                                        <n-grid-item>
                                            <n-statistic label="工作日值班">
                                                <n-number-animation :from="0" :to="selectedStaff.weekday_count" /> <template #suffix>天</template>
                                            </n-statistic>
                                        </n-grid-item>
                                        <n-grid-item>
                                            <n-statistic label="节假日值班">
                                                <span style="color: #d03050; font-weight: bold;">{{ selectedStaff.holiday_count }}</span> 天
                                            </n-statistic>
                                        </n-grid-item>
                                        <n-grid-item>
                                            <n-statistic label="周末值班">
                                                <span style="color: #f0a020; font-weight: bold;">{{ selectedStaff.weekend_count }}</span> 天
                                            </n-statistic>
                                        </n-grid-item>
                                    </n-grid>
                                </n-card>
                                
                                <n-grid :cols="2" x-gap="24">
                                    <n-grid-item>
                                        <n-card :bordered="false" class="shadow-card">
                                            <div id="chart-pie" style="height: 250px;"></div>
                                        </n-card>
                                    </n-grid-item>
                                    <n-grid-item>
                                        <n-card :bordered="false" class="shadow-card">
                                            <div id="chart-line" style="height: 250px;"></div>
                                        </n-card>
                                    </n-grid-item>
                                </n-grid>

                                <n-card title="📅 年度值班明细日历" :bordered="false" class="shadow-card">
                                    <n-grid :cols="6" x-gap="12" y-gap="12">
                                        <n-grid-item v-for="mItem in monthlyDetailsList" :key="mItem.month">
                                            <div class="month-box">
                                                <div class="month-title">{{ currentYear }}年{{ mItem.month }}月</div>
                                                <div class="duty-list">
                                                    <div v-if="mItem.details.length === 0" class="empty-month">-</div>
                                                    <n-tag v-for="d in mItem.details" :key="d.fullDate" :type="d.isHoliday ? 'error' : (d.isWeekend ? 'warning' : 'success')" size="small" style="margin: 2px;" :bordered="false">
                                                        {{ d.day }}日 [{{ d.typeShort }}]
                                                    </n-tag>
                                                </div>
                                            </div>
                                        </n-grid-item>
                                    </n-grid>
                                </n-card>
                            </n-space>
                        </n-grid-item>
                    </n-grid>
                </n-tab-pane>

                <n-tab-pane name="matrix" tab="📅 周番分布 (排除节假日)">
                    <n-card :bordered="false" class="shadow-card">
                        <table class="heatmap-table">
                            <thead>
                                <tr>
                                    <th style="width: 100px;">姓名</th>
                                    <th v-for="d in weekDays" :key="d">{{ d }}</th>
                                    <th style="width: 80px;">合计</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="row in advancedStats.weekday_stats" :key="row.name">
                                    <td class="name-cell">{{ row.name }}</td>
                                    <td v-for="(count, idx) in row.counts" :key="idx" :style="getHeatmapStyle(count)">
                                        {{ count > 0 ? count : '-' }}
                                    </td>
                                    <td style="font-weight: bold;">{{ row.total }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </n-card>
                </n-tab-pane>

                <n-tab-pane name="holidays" tab="🧧 节假日值班总览">
                    <n-grid x-gap="24" :cols="1">
                        <n-grid-item>
                            <n-card :bordered="false" class="info-card shadow-card">
                                <n-space justify="space-around">
                                    <n-statistic label="节假日总天数" :value="advancedStats.holiday_stats.total_days" />
                                    <n-statistic label="节假日值班总人次" :value="advancedStats.holiday_stats.total_duties" />
                                </n-space>
                            </n-card>
                        </n-grid-item>
                        <n-grid-item>
                            <div class="holiday-container">
                                <n-grid :cols="4" x-gap="16" y-gap="16">
                                    <n-grid-item v-for="(group, idx) in advancedStats.holiday_stats.groups" :key="idx">
                                        <n-card :title="group.name" size="small" class="holiday-card shadow-card" :header-style="{background: '#fff0f0', color: '#d03050'}">
                                            <div class="holiday-days">
                                                <div v-for="day in group.days" :key="day.date" class="day-row" :class="{ 'is-center': day.is_center }">
                                                    <div class="date-label">
                                                        {{ day.date.substring(5) }}
                                                        <span v-if="day.is_center" class="crown">👑</span>
                                                    </div>
                                                    <div class="staff-names">
                                                        <n-tag v-for="n in day.names" :key="n" size="small" :type="day.is_center ? 'warning' : 'default'">
                                                            {{ n }}
                                                        </n-tag>
                                                        <span v-if="day.names.length===0" style="color:#ccc;font-size:12px;">空</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </n-card>
                                    </n-grid-item>
                                </n-grid>
                            </div>
                        </n-grid-item>
                    </n-grid>
                </n-tab-pane>
            </n-tabs>
        </n-spin>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<style scoped>
.stats-container { background-color: #f5f7fa; min-height: 100vh; color: #333; }
.nav-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; border-bottom: 1px solid #e1e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo-text { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 20px; font-weight: 800; color: #2c3e50; }
.shadow-card { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.info-card { background: linear-gradient(135deg, #fff 0%, #f0f7ff 100%); }

.month-box { background: #f9f9f9; border-radius: 8px; padding: 8px; height: 100%; min-height: 80px; border: 1px solid #eee; }
.month-title { font-size: 14px; font-weight: bold; color: #666; margin-bottom: 4px; border-bottom: 1px solid #eee; padding-bottom: 2px; }
.duty-list { display: flex; flex-wrap: wrap; gap: 2px; }
.empty-month { color: #ccc; font-size: 12px; padding-left: 4px; }

.heatmap-table { width: 100%; border-collapse: collapse; text-align: center; }
.heatmap-table th { padding: 12px; background: #f5f7fa; border-bottom: 1px solid #eee; color: #666; font-weight: bold; }
.heatmap-table td { padding: 8px; border: 1px solid #eee; height: 40px; font-size: 14px; }
.name-cell { font-weight: bold; color: #333; background: #fff; text-align: left; padding-left: 16px !important; }

.holiday-card { border: 1px solid #fcebeb; }
.day-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f5f5f5; }
.day-row:last-child { border-bottom: none; }
.day-row.is-center { background-color: #fffbf0; padding: 6px 4px; border-radius: 4px; }
.date-label { font-weight: bold; color: #666; font-size: 13px; }
.crown { margin-left: 4px; font-size: 14px; }
.staff-names { display: flex; gap: 4px; }
</style>
