<template>
  <div class="tenant-detail">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="租户ID">{{ tenant.tenant_id }}</el-descriptions-item>
      <el-descriptions-item label="名称">{{ tenant.name }}</el-descriptions-item>
      <el-descriptions-item label="显示名称">{{ tenant.display_name }}</el-descriptions-item>
      <el-descriptions-item label="描述">{{ tenant.description }}</el-descriptions-item>
      <el-descriptions-item label="域名">{{ tenant.domain || '未设置' }}</el-descriptions-item>
      <el-descriptions-item label="等级">
        <el-tag :type="getTierType(tenant.tier)">{{ getTierText(tenant.tier) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(tenant.status)">{{ getStatusText(tenant.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="最大用户数">{{ tenant.max_users }}</el-descriptions-item>
      <el-descriptions-item label="最大存储(GB)">{{ tenant.max_storage_gb }}</el-descriptions-item>
      <el-descriptions-item label="每日API调用限制">{{ tenant.max_api_calls_per_day }}</el-descriptions-item>
      <el-descriptions-item label="功能模块" :span="2">
        <el-tag v-for="feature in tenant.features" :key="feature" size="small" style="margin-right: 4px">
          {{ feature }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDate(tenant.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ formatDate(tenant.updated_at) }}</el-descriptions-item>
      <el-descriptions-item label="过期时间" v-if="tenant.expires_at">
        {{ formatDate(tenant.expires_at) }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
import { ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus'
import type { Tenant } from '@/api/tenants'
import { formatDate } from '@/utils/datetime'

defineProps<{
  tenant: Tenant
}>()

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
</script>

