<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { 
    NLayout, NLayoutHeader, NLayoutContent, NCard, NDataTable, NButton, 
    NSpace, NInput, NModal, NForm, NFormItem, useMessage, NTag, NPopconfirm
} from 'naive-ui'
import request from '../utils/request'

const router = useRouter()
const message = useMessage()

// ================= 状态定义 =================
const loading = ref(false)
const contacts = ref([])
const searchText = ref('')
const currentUser = ref(null)

// 编辑相关状态
const showEditModal = ref(false)
const editForm = ref({ id: null, real_name: '', department: '', phone: '' })

// ================= 1. 初始化与权限 =================
const isAdmin = computed(() => {
    return currentUser.value && (currentUser.value.role === 'admin' || currentUser.value.role === 'super_admin')
})

function fetchUserInfo() {
    const token = localStorage.getItem('token')
    if (!token) { currentUser.value = null; return }
    try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        currentUser.value = { role: payload.role, username: payload.sub }
    } catch (e) { currentUser.value = null }
}

// ================= 2. 动态计算部门选项 (放在 columns 前面！) =================
const deptOptions = computed(() => {
    // 提取所有不为空的部门，去重，并格式化为 { label, value }
    const depts = [...new Set(contacts.value.map(c => c.department).filter(d => d))]
    return depts.map(d => ({ label: d, value: d }))
})

// ================= 3. 表格列定义 (包含筛选逻辑) =================
const columns = computed(() => {
    const cols = [
        { 
            title: '姓名', 
            key: 'real_name', 
            width: 120, 
            sorter: 'default' 
        },
        { 
            title: '部门', 
            key: 'department', 
            width: 150, 
            // 筛选配置
            filterOptions: deptOptions.value,
            filter: (value, row) => {
                // 如果 value 是用户选中的部门，row.department 必须等于它
                return row.department === value
            }
        },
        { 
            title: '联系电话', 
            key: 'phone', 
            width: 200 
        }
    ]

    // 只有管理员才显示操作列
    if (isAdmin.value) {
        cols.push({
            title: '操作',
            key: 'actions',
            width: 150,
            render(row) {
                return h(NSpace, null, {
                    default: () => [
                        h(NButton, {
                            size: 'small', type: 'primary', ghost: true,
                            onClick: () => openEdit(row)
                        }, { default: () => '编辑' }),
                        h(NPopconfirm, {
                            onPositiveClick: () => handleDelete(row.id)
                        }, {
                            trigger: () => h(NButton, { size: 'small', type: 'error', ghost: true }, { default: () => '删除' }),
                            default: () => '确定删除该人员吗？建议先清理相关排班。'
                        })
                    ]
                })
            }
        })
    }
    return cols
})

// ================= 4. 数据操作逻辑 =================
async function fetchContacts() {
    loading.value = true
    try {
        contacts.value = await request.get('/contacts/public')
    } catch (e) {
        message.error("获取通讯录失败")
    } finally {
        loading.value = false
    }
}

function openEdit(row) {
    editForm.value = { ...row }
    showEditModal.value = true
}

async function saveContact() {
    if (!editForm.value.real_name) return message.warning("姓名不能为空")
    try {
        await request.put(`/contacts/${editForm.value.id}`, {
            real_name: editForm.value.real_name,
            phone: editForm.value.phone,
            department: editForm.value.department
        })
        message.success("更新成功")
        showEditModal.value = false
        fetchContacts()
    } catch (e) {
        message.error("更新失败: " + (e.response?.data?.detail || "未知错误"))
    }
}

async function handleDelete(id) {
    try {
        await request.delete(`/contacts/${id}`)
        message.success("删除成功")
        fetchContacts()
    } catch (e) {
        message.error(e.response?.data?.detail || "删除失败")
    }
}

// 前端搜索逻辑 (配合搜索框)
const filteredData = computed(() => {
    if (!searchText.value) return contacts.value
    const lower = searchText.value.toLowerCase()
    return contacts.value.filter(item => 
        (item.real_name && item.real_name.includes(lower)) || 
        (item.phone && item.phone.includes(lower)) ||
        (item.department && item.department.includes(lower))
    )
})

onMounted(() => {
    fetchUserInfo()
    fetchContacts()
})
</script>

<template>
    <n-layout style="height: 100vh; background: #f5f7fa;">
        <n-layout-header class="nav-header">
            <div class="brand">
                <span class="logo-text">企业通讯录</span>
                <n-tag v-if="isAdmin" type="success" size="small" style="margin-left: 10px">管理员模式</n-tag>
            </div>
            <n-button secondary @click="router.push('/')">返回主页</n-button>
        </n-layout-header>

        <n-layout-content content-style="padding: 24px;">
            <n-card :bordered="false" style="border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <n-space vertical size="large">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 16px; font-weight: bold; color: #333;">全员联系方式</div>
                        <n-input v-model:value="searchText" placeholder="搜索姓名、电话或部门" style="width: 300px">
                            <template #prefix>🔍</template>
                        </n-input>
                    </div>

                    <n-data-table 
                        :columns="columns" 
                        :data="filteredData" 
                        :loading="loading" 
                        :pagination="{ pageSize: 15 }" 
                        striped
                    />
                </n-space>
            </n-card>
        </n-layout-content>

        <n-modal v-model:show="showEditModal" preset="card" title="编辑人员信息" style="width: 500px">
            <n-form label-placement="left" label-width="80">
                <n-form-item label="姓名">
                    <n-input v-model:value="editForm.real_name" placeholder="请输入姓名" />
                </n-form-item>
                <n-form-item label="部门">
                    <n-input v-model:value="editForm.department" placeholder="请输入部门" />
                </n-form-item>
                <n-form-item label="电话">
                    <n-input v-model:value="editForm.phone" placeholder="请输入联系电话" />
                </n-form-item>
            </n-form>
            <template #footer>
                <n-space justify="end">
                    <n-button @click="showEditModal = false">取消</n-button>
                    <n-button type="primary" @click="saveContact">保存修改</n-button>
                </n-space>
            </template>
        </n-modal>
    </n-layout>
</template>

<style scoped>
.nav-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; background: #fff; border-bottom: 1px solid #eee; }
.logo-text { font-size: 20px; font-weight: 800; color: #2c3e50; }
</style>
