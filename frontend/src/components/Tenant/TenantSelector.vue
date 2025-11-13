<template>
  <el-select
    v-model="selectedTenantId"
    placeholder="选择租户"
    clearable
    filterable
    @change="handleTenantChange"
    style="width: 200px"
  >
    <el-option
      v-for="tenant in tenants"
      :key="tenant.tenant_id"
      :label="tenant.display_name || tenant.name"
      :value="tenant.tenant_id"
    >
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>{{ tenant.display_name || tenant.name }}</span>
        <el-tag :type="getStatusType(tenant.status)" size="small" style="margin-left: 8px">
          {{ getStatusText(tenant.status) }}
        </el-tag>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElSelect, ElOption, ElTag } from 'element-plus'
import { useTenantStore } from '@/stores/tenant'
import type { Tenant } from '@/api/tenants'

const tenantStore = useTenantStore()

const selectedTenantId = ref<string | null>(null)
const tenants = ref<Tenant[]>([])

// 监听当前租户变化
watch(() => tenantStore.currentTenant, (tenant) => {
  selectedTenantId.value = tenant?.tenant_id || null
}, { immediate: true })

// 加载租户列表
const loadTenants = async () => {
  try {
    await tenantStore.loadTenants({ status: 'active' })
    tenants.value = tenantStore.tenants
  } catch (error) {
    console.error('加载租户列表失败:', error)
  }
}

// 处理租户切换
const handleTenantChange = async (tenantId: string | null) => {
  if (tenantId) {
    await tenantStore.switchTenant(tenantId)
  } else {
    tenantStore.clearTenant()
  }
}

// 获取状态类型
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

// 获取状态文本
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

