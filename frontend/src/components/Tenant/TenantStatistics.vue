<template>
  <div class="tenant-statistics" v-loading="loading">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="租户ID">{{ stats.tenant_id }}</el-descriptions-item>
      <el-descriptions-item label="名称">{{ stats.name }}</el-descriptions-item>
      <el-descriptions-item label="等级">
        <el-tag>{{ stats.tier }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(stats.status)">{{ stats.status }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="当前用户数">{{ stats.current_users }}</el-descriptions-item>
      <el-descriptions-item label="最大用户数">{{ stats.max_users }}</el-descriptions-item>
      <el-descriptions-item label="用户使用率" :span="2">
        <el-progress :percentage="stats.user_usage_percent" />
      </el-descriptions-item>
      <el-descriptions-item label="功能模块" :span="2">
        <el-tag v-for="feature in stats.features" :key="feature" size="small" style="margin-right: 4px">
          {{ feature }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElDescriptions, ElDescriptionsItem, ElTag, ElProgress } from 'element-plus'
import { getTenantStatistics } from '@/api/tenants'
import type { TenantStatistics } from '@/api/tenants'

const props = defineProps<{
  tenantId: string
}>()

const loading = ref(false)
const stats = ref<TenantStatistics>({
  tenant_id: '',
  name: '',
  tier: '',
  status: '',
  current_users: 0,
  max_users: 0,
  user_usage_percent: 0,
  features: [],
})

const loadStatistics = async () => {
  try {
    loading.value = true
    const response = await getTenantStatistics(props.tenantId)
    if (response.success) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  } finally {
    loading.value = false
  }
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

onMounted(() => {
  loadStatistics()
})
</script>

