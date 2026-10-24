import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AccountManagement from '../views/AccountManagement.vue'
import MaterialManagement from '../views/MaterialManagement.vue'
import PublishCenter from '../views/PublishCenter.vue'
import About from '../views/About.vue'
import TaskBoard from '../views/TaskBoard.vue'
import TaskComposer from '../views/TaskComposer.vue'
import SystemSettings from '../views/SystemSettings.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/account-management',
    name: 'AccountManagement',
    component: AccountManagement
  },
  {
    path: '/material-management',
    name: 'MaterialManagement',
    component: MaterialManagement
  },
  {
    path: '/publish-center',
    name: 'PublishCenter',
    component: PublishCenter
  },
  {
    path: '/about',
    name: 'About',
    component: About
  },
  {
    path: '/queue',
    name: 'Queue',
    component: TaskBoard,
    props: { mode: 'queue' }
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: TaskBoard,
    props: { mode: 'calendar' }
  },
  {
    path: '/history',
    name: 'History',
    component: TaskBoard,
    props: { mode: 'history' }
  },
  {
    path: '/new-task',
    name: 'NewTask',
    component: TaskComposer
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SystemSettings
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
