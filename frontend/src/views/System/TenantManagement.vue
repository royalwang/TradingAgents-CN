<template>
  <div class="tenant-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>租户管理</span>
          <div>
            <el-button type="primary" @click="handleImport">导入配置</el-button>
            <el-button @click="handleExport">导出配置</el-button>
            <el-button @click="loadTenants">刷新</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="输入租户名称或ID"
            clearable
            @keyup.enter="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="活跃" value="active" />
            <el-option label="非活跃" value="inactive" />
            <el-option label="已暂停" value="suspended" />
            <el-option label="试用" value="trial" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="searchForm.tier" placeholder="全部" clearable style="width: 120px">
            <el-option label="免费" value="free" />
            <el-option label="基础" value="basic" />
            <el-option label="专业" value="professional" />
            <el-option label="企业" value="enterprise" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 租户列表 -->
      <el-table v-loading="loading" :data="tenants" stripe>
        <el-table-column prop="tenant_id" label="租户ID" width="150" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="tier" label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getTierType(row.tier)">{{ getTierText(row.tier) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_users" label="最大用户数" width="120" />
        <el-table-column prop="features" label="功能模块" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="feature in row.features"
              :key="feature"
              size="small"
              style="margin-right: 4px"
            >
              {{ feature }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="primary" link @click="handleStatistics(row)">统计</el-button>
            <el-button type="warning" link @click="handleStatusChange(row)">状态</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 租户详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="租户详情" width="800px">
      <tenant-detail v-if="selectedTenant" :tenant="selectedTenant" />
    </el-dialog>

    <!-- 统计信息对话框 -->
    <el-dialog v-model="statisticsDialogVisible" title="租户统计" width="600px">
      <tenant-statistics v-if="selectedTenant" :tenant-id="selectedTenant.tenant_id" />
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入租户配置" width="600px">
      <tenant-import @success="handleImportSuccess" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTenantStore } from '@/stores/tenant'
import { updateTenantStatus, exportTenantsToYaml } from '@/api/tenants'
import type { Tenant } from '@/api/tenants'
import TenantDetail from '@/components/Tenant/TenantDetail.vue'
import TenantStatistics from '@/components/Tenant/TenantStatistics.vue'
import TenantImport from '@/components/Tenant/TenantImport.vue'

const tenantStore = useTenantStore()

const loading = ref(false)
const tenants = ref<Tenant[]>([])
const selectedTenant = ref<Tenant | null>(null)

const searchForm = reactive({
  search: '',
  status: '',
  tier: '',
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0,
})

const detailDialogVisible = ref(false)
const statisticsDialogVisible = ref(false)
const importDialogVisible = ref(false)

// 加载租户列表
const loadTenants = async () => {
  try {
    loading.value = true
    const params: any = {
      ...searchForm,
    }
    const response = await tenantStore.loadTenants(params)
    if (response.success) {
      tenants.value = response.data.tenants
      pagination.total = response.data.count
    }
  } catch (error) {
    ElMessage.error('加载租户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadTenants()
}

// 重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.status = ''
  searchForm.tier = ''
  handleSearch()
}

// 查看详情
const handleView = (tenant: Tenant) => {
  selectedTenant.value = tenant
  detailDialogVisible.value = true
}

// 查看统计
const handleStatistics = (tenant: Tenant) => {
  selectedTenant.value = tenant
  statisticsDialogVisible.value = true
}

// 更改状态
const handleStatusChange = async (tenant: Tenant) => {
  try {
    const { value: status } = await ElMessageBox.prompt(
      '选择新状态',
      '更改租户状态',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'select',
        inputOptions: {
          active: '活跃',
          inactive: '非活跃',
          suspended: '已暂停',
          trial: '试用',
          expired: '已过期',
        },
        inputValue: tenant.status,
      }
    )
    
    await updateTenantStatus(tenant.tenant_id, status)
    ElMessage.success('状态更新成功')
    loadTenants()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('状态更新失败')
    }
  }
}

// 导入
const handleImport = () => {
  importDialogVisible.value = true
}

// 导出
const handleExport = async () => {
  try {
    const response = await exportTenantsToYaml(searchForm.status, searchForm.tier)
    if (response.success) {
      const blob = new Blob([response.data.yaml], { type: 'text/yaml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tenants_${new Date().getTime()}.yaml`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 导入成功
const handleImportSuccess = () => {
  importDialogVisible.value = false
  loadTenants()
}

// 分页
const handleSizeChange = () => {
  loadTenants()
}

const handlePageChange = () => {
  loadTenants()
}

// 工具函数
const getTierType = (tier: string) => {
  const tierMap: Record<string, string> = {
    free: 'info',
    basic: '',
    professional: 'success',
    enterprise: 'warning',
  }
  return tierMap[tier] || ''
}

const getTierText = (tier: string) => {
  const tierMap: Record<string, string> = {
    free: '免费',
    basic: '基础',
    professional: '专业',
    enterprise: '企业',
  }
  return tierMap[tier] || tier
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    active: 'success',
    inactive: 'info',
    suspended: 'warning',
    trial: 'warning',
    expired: 'danger',
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '活跃',
    inactive: '非活跃',
    suspended: '已暂停',
    trial: '试用',
    expired: '已过期',
  }
  return statusMap[status] || status
}

onMounted(() => {
  loadTenants()
})
</script>

<style scoped lang="scss">
.tenant-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }
}
</style>

