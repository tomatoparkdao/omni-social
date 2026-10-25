<template>
  <div id="app">
    <div v-if="!auth.ready" class="auth-shell">
      <div class="auth-boot">正在连接 OmniSocial…</div>
    </div>
    <div v-else-if="!auth.authenticated" class="auth-shell">
      <el-card class="auth-card">
        <h2>OmniSocial</h2>
        <p>请输入管理员密码以访问运营工作台</p>
        <el-form @submit.prevent="submitPassword">
          <el-input v-model="password" type="password" show-password autocomplete="current-password" placeholder="管理员密码" />
          <el-button type="primary" native-type="submit" :loading="authLoading">登录</el-button>
        </el-form>
      </el-card>
    </div>
    <el-container v-else>
      <el-aside :class="{ 'is-collapsed': isCollapse }" :width="isCollapse ? '64px' : '232px'">
        <div class="sidebar">
          <div class="logo">
            <img class="logo-mark" src="/omniailab-icon.svg" alt="Omni AiLab">
            <div v-show="!isCollapse" class="brand-copy">
              <h2>OmniSocial</h2>
              <span>内容运营工作台</span>
            </div>
          </div>
          <el-menu
            :router="true"
            :default-active="activeMenu"
            :collapse="isCollapse"
            class="sidebar-menu"
            background-color="#0b0c0d"
            text-color="#91959d"
            active-text-color="#f7f7f7"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/account-management">
              <el-icon><User /></el-icon>
              <span>账号管理</span>
            </el-menu-item>
            <el-menu-item index="/material-management">
              <el-icon><Picture /></el-icon>
              <span>素材管理</span>
            </el-menu-item>
            <el-menu-item index="/publish-center">
              <el-icon><Upload /></el-icon>
              <span>发布中心</span>
            </el-menu-item>
            <el-menu-item index="/new-task"><el-icon><EditPen /></el-icon><span>新建任务</span></el-menu-item>
            <el-menu-item index="/queue"><el-icon><List /></el-icon><span>发布队列</span></el-menu-item>
            <el-menu-item index="/calendar"><el-icon><Calendar /></el-icon><span>发布日历</span></el-menu-item>
            <el-menu-item index="/history"><el-icon><Clock /></el-icon><span>历史记录</span></el-menu-item>
            <el-menu-item index="/settings"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
            <el-menu-item index="/about">
              <el-icon><DataAnalysis /></el-icon>
              <span>关于</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <div class="crumb"><span>OmniSocial</span><b>/</b><strong>{{ pageTitle }}</strong></div>
              <el-icon class="toggle-sidebar" @click="toggleSidebar"><Fold /></el-icon>
            </div>
            <div class="header-right">
              <!-- 账号信息已移除 -->
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { authState as auth, loadSession, signIn } from '@/utils/auth'
import { ElMessage } from 'element-plus'
import {
  HomeFilled, User, DataAnalysis,
  Fold, Picture, Upload, List, Calendar, Clock, EditPen, Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const authLoading = ref(false)
const password = ref('')

onMounted(async () => {
  await loadSession()
  if (auth.error) ElMessage.error(auth.error)
})

const submitPassword = async () => {
  authLoading.value = true
  try {
    await signIn(password.value)
    password.value = ''
  } catch {
    password.value = ''
  } finally {
    authLoading.value = false
  }
}

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})
const pageTitle = computed(() => ({
  '/': '运营概览',
  '/account-management': '账号管理',
  '/material-management': '素材管理',
  '/publish-center': '发布中心',
  '/queue': '发布队列',
  '/calendar': '发布日历',
  '/history': '历史记录',
  '/new-task': '新建任务',
  '/settings': '系统设置',
  '/about': '系统信息'
}[route.path] || '运营工作台'))

// 侧边栏折叠状态
const isCollapse = ref(false)

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

#app {
  min-height: 100vh;
}

.auth-shell { min-height: 100vh; display: grid; place-items: center; background: #0f1113; }
.auth-boot { color: #91959d; font-size: 13px; letter-spacing: 0.04em; }
.auth-card { width: min(380px, calc(100vw - 32px)); }
.auth-card h2 { margin: 0 0 12px; }
.auth-card p { margin-bottom: 24px; }
.auth-card .el-button { width: 100%; margin-top: 16px; }

.el-container {
  height: 100vh;
}

.el-aside {
  background-color: #0b0c0d;
  color: #fff;
  height: 100vh;
  flex: 0 0 232px;
  min-width: 232px;
  overflow: hidden;
  transition: width 0.3s;

  &.is-collapsed {
    flex-basis: 64px;
    min-width: 64px;
  }
  
  .sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;
    
    .logo {
      height: 60px;
      padding: 0 16px;
      display: flex;
      align-items: center;
      background-color: #0b0c0d;
      overflow: hidden;
      
      .logo-mark {
        width: 30px;
        height: 30px;
        margin-right: 12px;
        display: grid;
        place-items: center;
        border-radius: 8px;
        background: #c8ff00;
      }
      
      .brand-copy h2 {
        color: #f7f7f7;
        font-size: 15px;
        font-weight: 600;
        white-space: nowrap;
        margin: 0;
      }
      .brand-copy span {
        display: block;
        margin-top: 3px;
        color: #91959d;
        font-size: 11px;
      }
    }
    
    .sidebar-menu {
      border-right: none;
      flex: 1;
      
      .el-menu-item {
        display: flex;
        align-items: center;
        
        .el-icon {
          margin-right: 10px;
          font-size: 18px;
        }
        &.is-active { background: #292929; border-right: 2px solid #c8ff00; }
      }
    }
  }
}

.el-header {
  background-color: #0f1113;
  border-bottom: 1px solid #2b2b2b;
  padding: 0;
  height: 60px;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    padding: 0 16px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 18px;
      .crumb { color: #91959d; font-size: 12px; b { margin: 0 8px; color: #4a4a4a; } strong { color: #f7f7f7; font-weight: 600; } }
      .toggle-sidebar {
        font-size: 20px;
        cursor: pointer;
        color: $text-regular;
        
        &:hover {
          color: $primary-color;
        }
      }
    }
    
    .header-right {
      .user-dropdown {
        display: flex;
        align-items: center;
        cursor: pointer;
        
        .username {
          margin: 0 8px;
          color: $text-regular;
        }
        
        .el-icon {
          font-size: 12px;
          color: $text-secondary;
        }
      }
    }
  }
}

.el-main {
  background-color: $bg-color-page;
  padding: 28px;
  overflow-y: auto;
}
</style>
