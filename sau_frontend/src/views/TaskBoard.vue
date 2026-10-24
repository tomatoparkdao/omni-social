<template>
  <div class="task-board">
    <div class="page-header">
      <h1>{{ titles[mode] }}</h1>
      <el-button @click="refresh" :loading="loading">刷新</el-button>
    </div>
    <el-alert v-if="mode === 'queue'" title="真实发布当前关闭。这里保存的是可核对的任务草稿，不会自动提交到平台。" type="warning" :closable="false" />
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <el-table :data="visibleTasks" v-loading="loading" empty-text="暂无真实任务记录" class="task-table">
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column label="平台" width="100">
        <template #default="{ row }">{{ platformNames[row.platform] || row.platform }}</template>
      </el-table-column>
      <el-table-column label="账号" width="150">
        <template #default="{ row }">{{ accountName(row.account_id) }}</template>
      </el-table-column>
      <el-table-column label="内容" width="90">
        <template #default="{ row }">{{ row.content_type === 'note' ? '图文' : '视频' }}</template>
      </el-table-column>
      <el-table-column v-if="mode === 'calendar'" label="安排时间" min-width="180">
        <template #default="{ row }">{{ formatTime(row.schedule_at) }}</template>
      </el-table-column>
      <el-table-column v-else label="创建时间" min-width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="130">
        <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ statusNames[row.status] || row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column v-if="mode === 'history'" label="失败原因" min-width="150">
        <template #default="{ row }">{{ row.error_code || '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button text @click="selected = row">查看</el-button>
          <el-button v-if="mode === 'queue' && ['draft', 'queued_mock', 'queued'].includes(row.status)" text type="danger" @click="cancel(row)">取消</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="detailOpen" title="任务详情" width="600px">
      <template v-if="selected">
        <p>标题：{{ selected.title }}</p>
        <p>正文：{{ selected.body || '未填写' }}</p>
        <p>话题：{{ selected.tags.join('、') || '无' }}</p>
        <p>素材：{{ selected.material_ids.map(materialName).join('、') }}</p>
        <p>计划时间：{{ formatTime(selected.schedule_at) }}</p>
        <p>任务 ID：{{ selected.id }}</p>
        <el-alert title="此处为发布前任务记录，不代表平台已发布。" type="info" :closable="false" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/utils/request'

const props = defineProps({ mode: { type: String, required: true } })
const titles = { queue: '发布队列', calendar: '发布日历', history: '历史记录' }
const platformNames = { 1: '小红书', 2: '视频号', 3: '抖音', 4: '快手' }
const statusNames = { draft: '待确认草稿', queued: '待执行', running: '执行中', submitted_unverified: '提交结果待核验', failed: '执行前失败', needs_review: '执行结果不确定', queued_mock: '模拟排队', running_mock: '模拟执行中', succeeded_mock: '模拟成功', failed_mock: '模拟失败', cancelled: '已取消' }
const loading = ref(false)
const error = ref('')
const tasks = ref([])
const accounts = ref([])
const materials = ref([])
const selected = ref(null)
const detailOpen = computed({ get: () => selected.value !== null, set: value => { if (!value) selected.value = null } })
const visibleTasks = computed(() => {
  if (props.mode === 'calendar') return tasks.value.filter(task => task.schedule_at).sort((a, b) => a.schedule_at.localeCompare(b.schedule_at))
  if (props.mode === 'history') return tasks.value.filter(task => ['submitted_unverified', 'failed', 'needs_review', 'succeeded_mock', 'failed_mock', 'cancelled'].includes(task.status))
  return tasks.value
})
const accountName = id => accounts.value.find(account => account[0] === id)?.[3] || `账号 #${id}`
const materialName = id => materials.value.find(material => material.id === id)?.filename || `素材 #${id}`
const formatTime = value => value ? new Date(value).toLocaleString('zh-CN') : '未安排'
const statusType = status => ({ draft: 'info', cancelled: 'warning', failed: 'danger', failed_mock: 'danger', needs_review: 'warning', submitted_unverified: 'warning', succeeded_mock: 'success' }[status] || 'info')

const refresh = async () => {
  loading.value = true
  error.value = ''
  try {
    const [taskResponse, accountResponse, materialResponse] = await Promise.all([
      http.get('/tasks'), http.get('/getAccounts'), http.get('/getFiles')
    ])
    tasks.value = taskResponse.data
    accounts.value = accountResponse.data
    materials.value = materialResponse.data
  } catch (exc) {
    error.value = `任务记录加载失败：${exc.message}`
  } finally {
    loading.value = false
  }
}
const cancel = async task => {
  try {
    await http.post(`/tasks/${task.id}/cancel`)
    ElMessage.success('任务已取消')
    await refresh()
  } catch (exc) {
    ElMessage.error(`取消失败：${exc.message}`)
  }
}
onMounted(refresh)
watch(() => props.mode, refresh)
</script>

<style scoped>
.task-board { color: #f7f7f7; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 24px; }
.task-table { margin-top: 20px; }
</style>
