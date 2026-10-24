<template>
  <div class="settings-page">
    <h1>系统设置</h1>
    <el-alert title="敏感账号会话只保存在服务端，不提供网页下载或直接覆盖。真实发布默认关闭。" type="warning" :closable="false" />
    <el-card v-loading="loading" class="status-card">
      <template #header>运行状态</template>
      <p>环境：{{ status.mode === 'production' ? '生产' : '本地开发' }}</p>
      <p>数据库：{{ status.database_ready ? '可用' : '未就绪' }}</p>
      <p>素材目录：{{ status.material_storage_ready ? '可用' : '未就绪' }}</p>
      <p>浏览器自动化依赖：{{ status.browser_library_ready ? '已安装' : '未安装' }}</p>
      <p>真实发布：{{ status.real_publish_enabled ? '已启用' : '已关闭' }}</p>
      <el-button @click="refresh">刷新状态</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/utils/request'

const status = ref({})
const loading = ref(false)
const refresh = async () => {
  loading.value = true
  try {
    status.value = (await http.get('/system/status')).data
  } catch (error) {
    ElMessage.error(`状态检查失败：${error.message}`)
  } finally {
    loading.value = false
  }
}
onMounted(refresh)
</script>

<style scoped>
.settings-page { max-width: 800px; color: #f7f7f7; }
.settings-page h1 { font-size: 24px; margin: 0 0 20px; }
.status-card { margin-top: 20px; }
</style>
