/**
 * 租户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Tenant } from '@/api/tenants'
import { getTenants, getTenant } from '@/api/tenants'
import { useStorage } from '@vueuse/core'

export const useTenantStore = defineStore('tenant', () => {
  // 当前租户
  const currentTenant = useStorage<Tenant | null>('current-tenant', null)
  
  // 租户列表
  const tenants = ref<Tenant[]>([])
  const loading = ref(false)

  // 计算属性
  const hasTenant = computed(() => currentTenant.value !== null)
  const tenantId = computed(() => currentTenant.value?.tenant_id || null)
  const tenantTier = computed(() => currentTenant.value?.tier || null)
  const tenantFeatures = computed(() => currentTenant.value?.features || [])

  // 检查功能是否启用
  const hasFeature = (feature: string): boolean => {
    return tenantFeatures.value.includes(feature)
  }

  // 设置当前租户
  const setCurrentTenant = (tenant: Tenant | null) => {
    currentTenant.value = tenant
  }

  // 加载租户列表
  const loadTenants = async (params?: { status?: string; tier?: string; search?: string }) => {
    try {
      loading.value = true
      const response = await getTenants(params)
      if (response.success) {
        tenants.value = response.data.tenants
      }
      return response
    } catch (error) {
      console.error('加载租户列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 加载租户详情
  const loadTenant = async (tenantId: string) => {
    try {
      loading.value = true
      const response = await getTenant(tenantId)
      if (response.success) {
        return response.data
      }
      return null
    } catch (error) {
      console.error('加载租户详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 切换租户
  const switchTenant = async (tenantId: string) => {
    const tenant = await loadTenant(tenantId)
    if (tenant) {
      setCurrentTenant(tenant)
      // 可以在这里触发其他操作，比如重新加载用户数据等
      return true
    }
    return false
  }

  // 清除当前租户
  const clearTenant = () => {
    currentTenant.value = null
  }

  return {
    // 状态
    currentTenant,
    tenants,
    loading,
    // 计算属性
    hasTenant,
    tenantId,
    tenantTier,
    tenantFeatures,
    // 方法
    hasFeature,
    setCurrentTenant,
    loadTenants,
    loadTenant,
    switchTenant,
    clearTenant,
  }
})

