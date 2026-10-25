import { reactive } from 'vue'
import { http } from '@/utils/request'

/**
 * 会话状态由服务端 /auth/session 决定：
 * - mode=local_dev：服务端已声明免登录，前端直接进入工作台；
 * - mode=production：必须通过管理员密码登录。
 * 前端不做任何基于 IP / 环境变量的自动放行。
 */
export const authState = reactive({
  ready: false,
  authenticated: false,
  mode: 'production',
  error: ''
})

let pending = null

export function loadSession() {
  if (!pending) {
    pending = http
      .get('/auth/session')
      .then((state) => {
        authState.authenticated = state.authenticated === true
        authState.mode = state.mode || 'production'
        authState.error = ''
        return authState
      })
      .catch(() => {
        authState.authenticated = false
        authState.error = '无法检查服务端登录状态'
        return authState
      })
      .finally(() => {
        authState.ready = true
        pending = null
      })
  }
  return pending
}

export async function signIn(password) {
  const state = await http.post('/auth/session', { password })
  authState.authenticated = state.authenticated === true
  authState.mode = state.mode || authState.mode
  authState.ready = true
  authState.error = ''
  return authState
}

export function markUnauthenticated() {
  if (authState.mode === 'local_dev') return
  authState.authenticated = false
  authState.ready = true
}

// 任意接口返回 401 时回到登录页（本地免登录模式不会触发）。
window.addEventListener('omnisocial:unauthorized', markUnauthenticated)
