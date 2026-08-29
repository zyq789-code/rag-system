/// <reference types="vite/client" />

// 让 vue-tsc 能解析 .vue 单文件组件导入（生产构建必需）
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const component: DefineComponent<{}, {}, any>
  export default component
}
