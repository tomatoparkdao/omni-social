<template>
  <div id="app">
    <el-container>
      <el-aside :class="{ 'is-collapsed': isCollapse }" :width="isCollapse ? '64px' : '232px'">
        <div class="sidebar">
          <div class="logo">
            <img class="logo-mark" src="https://wuxianhuabu123454.tos-cn-beijing.volces.com/public/site/20260727-v1/brand/omniailab-icon.svg" alt="Omni AiLab">
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
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled, User, DataAnalysis,
  Fold, Picture, Upload
} from '@element-plus/icons-vue'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})
const pageTitle = computed(() => ({
  '/': '运营概览',
  '/account-management': '账号管理',
  '/material-management': '素材管理',
  '/publish-center': '发布中心',
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
