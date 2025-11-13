<template>
  <div class="tenant-import">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="YAML文件" name="file">
        <el-upload
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          accept=".yaml,.yml"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">支持 .yaml 或 .yml 文件</div>
          </template>
        </el-upload>
        <el-checkbox v-model="updateExisting" style="margin-top: 10px">
          更新已存在的租户
        </el-checkbox>
        <el-button type="primary" @click="handleImportFile" :disabled="!selectedFile" style="margin-top: 10px; width: 100%">
          导入
        </el-button>
      </el-tab-pane>
      <el-tab-pane label="YAML文本" name="text">
        <el-input
          v-model="yamlText"
          type="textarea"
          :rows="15"
          placeholder="粘贴YAML配置内容"
        />
        <el-checkbox v-model="updateExisting" style="margin-top: 10px">
          更新已存在的租户
        </el-checkbox>
        <el-button type="primary" @click="handleImportText" :disabled="!yamlText" style="margin-top: 10px; width: 100%">
          导入
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importTenantsFromYamlFile, importTenantsFromYaml } from '@/api/tenants'
import type { UploadFile } from 'element-plus'

const emit = defineEmits<{
  success: []
}>()

const activeTab = ref('file')
const fileList = ref<UploadFile[]>([])
const selectedFile = ref<File | null>(null)
const yamlText = ref('')
const updateExisting = ref(false)

const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file.raw as File
}

const handleImportFile = async () => {
  if (!selectedFile.value) return
  
  try {
    const response = await importTenantsFromYamlFile(selectedFile.value, updateExisting.value)
    if (response.success) {
      ElMessage.success('导入成功')
      emit('success')
    }
  } catch (error) {
    ElMessage.error('导入失败')
  }
}

const handleImportText = async () => {
  if (!yamlText.value) return
  
  try {
    const response = await importTenantsFromYaml(yamlText.value, updateExisting.value)
    if (response.success) {
      ElMessage.success('导入成功')
      emit('success')
    }
  } catch (error) {
    ElMessage.error('导入失败')
  }
}
</script>

