<template>
  <div class="task-composer">
    <h1>新建发布任务</h1>
    <el-form label-position="top" class="composer-form">
      <el-form-item label="内容类型">
        <el-radio-group v-model="form.contentType" @change="changeContentType">
          <el-radio-button value="note">图文</el-radio-button>
          <el-radio-button value="video">视频</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="目标平台">
        <el-select v-model="form.platform" @change="form.accountIds = []">
          <el-option v-for="platform in availablePlatforms" :key="platform.id" :label="platform.name" :value="platform.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="账号">
        <el-checkbox-group v-model="form.accountIds">
          <el-checkbox v-for="account in matchingAccounts" :key="account[0]" :value="account[0]" :label="account[3]" />
        </el-checkbox-group>
        <el-text v-if="!matchingAccounts.length" type="info">此平台暂无账号，请先在账号管理中添加。</el-text>
      </el-form-item>
      <el-form-item label="标题"><el-input v-model="form.title" maxlength="200" show-word-limit /></el-form-item>
      <el-form-item label="正文"><el-input v-model="form.body" type="textarea" :rows="5" maxlength="10000" show-word-limit /></el-form-item>
      <el-form-item label="话题"><el-input v-model="form.tags" placeholder="用逗号分隔，不需要 #" /></el-form-item>
      <el-form-item label="素材">
        <el-checkbox-group v-model="form.materialIds" class="material-list">
          <el-checkbox v-for="material in matchingMaterials" :key="material.id" :value="material.id" :label="material.filename" />
        </el-checkbox-group>
        <el-text v-if="!matchingMaterials.length" type="info">暂无匹配素材，请先在素材管理上传。</el-text>
      </el-form-item>
      <el-form-item label="安排时间（可选）"><el-date-picker v-model="form.scheduleAt" type="datetime" placeholder="不安排则只保存草稿" /></el-form-item>
      <div class="actions">
        <el-button @click="previewOpen = true">发布前预览</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存任务草稿</el-button>
      </div>
    </el-form>
    <el-dialog v-model="previewOpen" title="发布前预览" width="680px">
      <h2>{{ form.title || '未填写标题' }}</h2>
      <p>{{ form.body || '未填写正文' }}</p>
      <p>平台：{{ platforms.find(item => item.id === form.platform)?.name || '未选择' }}</p>
      <p>目标账号：{{ form.accountIds.map(id => accounts.find(item => item[0] === id)?.[3]).join('、') || '未选择' }}</p>
      <p>话题：{{ form.tags || '无' }}</p>
      <p>安排时间：{{ form.scheduleAt?.toLocaleString('zh-CN') || '未安排' }}</p>
      <div v-for="material in selectedMaterials" :key="material.id" class="preview-media">
        <img v-if="form.contentType === 'note'" :src="materialUrl(material)" :alt="material.filename" />
        <video v-else :src="materialUrl(material)" controls preload="metadata" />
        <div>{{ material.filename }}</div>
      </div>
      <el-alert title="预览不代表平台最终效果；未触发真实发布。" type="info" :closable="false" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/utils/request'

const platforms = [{ id: 1, name: '小红书' }, { id: 2, name: '视频号' }, { id: 3, name: '抖音' }, { id: 4, name: '快手' }]
const accounts = ref([])
const materials = ref([])
const saving = ref(false)
const previewOpen = ref(false)
const form = reactive({ contentType: 'note', platform: 1, accountIds: [], title: '', body: '', tags: '', materialIds: [], scheduleAt: null, key: null })
const availablePlatforms = computed(() => form.contentType === 'note' ? platforms.filter(item => item.id !== 2) : platforms)
const matchingAccounts = computed(() => accounts.value.filter(item => item[1] === form.platform))
const matchingMaterials = computed(() => materials.value.filter(item => {
  const suffix = item.filename?.toLowerCase().split('.').pop()
  return form.contentType === 'note' ? ['jpg', 'jpeg', 'png', 'webp'].includes(suffix) : ['mp4', 'mov', 'avi', 'mkv', 'm4v', 'webm'].includes(suffix)
}))
const selectedMaterials = computed(() => materials.value.filter(item => form.materialIds.includes(item.id)))
const materialUrl = material => `${import.meta.env.VITE_API_BASE_URL || '/api'}/getFile?filename=${encodeURIComponent(material.file_path)}`
const changeContentType = () => {
  form.materialIds = []
  form.accountIds = []
  if (form.contentType === 'note' && form.platform === 2) form.platform = 1
}

onMounted(async () => {
  try {
    const [accountResponse, materialResponse] = await Promise.all([http.get('/getAccounts'), http.get('/getFiles')])
    accounts.value = accountResponse.data
    materials.value = materialResponse.data
  } catch (error) {
    ElMessage.error(`加载账号或素材失败：${error.message}`)
  }
})

const save = async () => {
  if (!form.accountIds.length || !form.materialIds.length || !form.title.trim()) {
    ElMessage.error('请填写标题并选择账号和素材')
    return
  }
  if (form.contentType === 'video' && form.materialIds.length !== 1) {
    ElMessage.error('视频任务只能选择一个视频素材')
    return
  }
  saving.value = true
  form.key ||= crypto.randomUUID()
  try {
    for (const accountId of form.accountIds) {
      await http.post('/tasks', {
        platform: form.platform,
        account_id: accountId,
        content_type: form.contentType,
        title: form.title.trim(),
        body: form.body,
        tags: form.tags.split(/[,，]/).map(item => item.trim().replace(/^#/, '')).filter(Boolean),
        material_ids: form.materialIds,
        schedule_at: form.scheduleAt?.toISOString() || null,
        idempotency_key: `${form.key}:${accountId}`
      })
    }
    ElMessage.success('任务草稿已保存，未执行真实发布')
    form.key = null
  } catch (error) {
    ElMessage.error(`保存失败：${error.message}。重试不会重复创建已保存的任务`)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.task-composer { max-width: 900px; color: #f7f7f7; }
.task-composer h1 { font-size: 24px; margin: 0 0 20px; }
.composer-form { margin-top: 24px; }
.material-list { display: flex; flex-direction: column; max-height: 240px; overflow-y: auto; }
.actions { display: flex; gap: 12px; }
.preview-media { margin: 12px 0; }
.preview-media img, .preview-media video { max-width: 100%; max-height: 300px; }
</style>
