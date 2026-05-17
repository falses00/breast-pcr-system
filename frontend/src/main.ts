import { createApp } from 'vue'
import {
  ElAlert,
  ElAside,
  ElButton,
  ElContainer,
  ElDialog,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElSelect,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElUpload,
} from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'
import App from './App.vue'
import { router } from './router'

const app = createApp(App)
const elementComponents = [
  ElAlert,
  ElAside,
  ElButton,
  ElContainer,
  ElDialog,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElSelect,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElUpload,
]

elementComponents.forEach((component) => app.use(component))
app.use(router).mount('#app')
