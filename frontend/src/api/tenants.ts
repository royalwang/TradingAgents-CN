/**
 * 租户管理API
 */
import request from './request'
import type { ApiResponse } from './request'

export interface Tenant {
  tenant_id: string
  name: string
  display_name: string
  description: string
  domain?: string
  tier: 'free' | 'basic' | 'professional' | 'enterprise'
  status: 'active' | 'inactive' | 'suspended' | 'trial' | 'expired'
  max_users: number
  max_storage_gb: number
  max_api_calls_per_day: number
  features: string[]
  config: Record<string, any>
  metadata: Record<string, any>
  owner_id?: string
  created_at: string
  updated_at: string
  expires_at?: string
}

export interface TenantStatistics {
  tenant_id: string
  name: string
  tier: string
  status: string
  current_users: number
  max_users: number
  user_usage_percent: number
  features: string[]
}

export interface TenantListParams {
  status?: string
  tier?: string
  search?: string
}

/**
 * 列出租户
 */
export const getTenants = (params?: TenantListParams): Promise<ApiResponse<{ tenants: Tenant[], count: number }>> => {
  return request.get('/api/platform/tenants', { params })
}

/**
 * 获取租户详情
 */
export const getTenant = (tenantId: string): Promise<ApiResponse<Tenant>> => {
  return request.get(`/api/platform/tenants/${tenantId}`)
}

/**
 * 获取租户统计信息
 */
export const getTenantStatistics = (tenantId: string): Promise<ApiResponse<TenantStatistics>> => {
  return request.get(`/api/platform/tenants/${tenantId}/statistics`)
}

/**
 * 更新租户状态
 */
export const updateTenantStatus = (tenantId: string, status: string): Promise<ApiResponse<{ success: boolean, status: string }>> => {
  return request.post(`/api/platform/tenants/${tenantId}/status`, null, { params: { status } })
}

/**
 * 从YAML字符串导入租户配置
 */
export const importTenantsFromYaml = (yamlStr: string, updateExisting: boolean = false): Promise<ApiResponse<any>> => {
  return request.post('/api/platform/tenants/import/yaml', { yaml_str: yamlStr, update_existing: updateExisting })
}

/**
 * 从YAML文件导入租户配置
 */
export const importTenantsFromYamlFile = (file: File, updateExisting: boolean = false): Promise<ApiResponse<any>> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('update_existing', String(updateExisting))
  return request.post('/api/platform/tenants/import/yaml-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 导出租户配置为YAML格式
 */
export const exportTenantsToYaml = (status?: string, tier?: string): Promise<ApiResponse<{ yaml: string }>> => {
  return request.get('/api/platform/tenants/export/yaml', {
    params: { status, tier }
  })
}

