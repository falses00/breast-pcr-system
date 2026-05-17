import type {
  AnalysisDetail,
  AnalysisTask,
  AnnotationRecord,
  AnnotationPayload,
  AuditRecord,
  ClinicalRecord,
  FeatureImportance,
  ImageRecord,
  LoginResponse,
  ModelMetric,
  Patient,
  ROIFeatureDetail,
  StatsSummary,
  UserRecord,
} from './types'

const API_BASE = '/api'

function token() {
  return localStorage.getItem('pcr_token') || ''
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token()) headers.set('Authorization', `Bearer ${token()}`)
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    const text = await res.text()
    let message = ''
    try {
      const payload = JSON.parse(text)
      message = payload.message || payload.detail || ''
    } catch {
      message = text
    }
    throw new Error(message || `请求失败：${res.status}`)
  }
  return res.json()
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  me: () => request<LoginResponse['user']>('/auth/me'),
  patients: (keyword?: string) => request<Patient[]>(`/patients${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`),
  createPatient: (payload: Partial<Patient>) => request<Patient>('/patients', { method: 'POST', body: JSON.stringify(payload) }),
  createClinical: (patientId: number, payload: Partial<ClinicalRecord>) =>
    request<ClinicalRecord>(`/patients/${patientId}/clinical`, { method: 'POST', body: JSON.stringify(payload) }),
  images: (patientId?: number) => request<ImageRecord[]>(`/images${patientId ? `?patient_id=${patientId}` : ''}`),
  uploadImage: (patientId: number, file: File) => {
    const form = new FormData()
    form.set('file', file)
    return request<ImageRecord>(`/images/upload?patient_id=${patientId}`, { method: 'POST', body: form })
  },
  createAnnotation: (payload: AnnotationPayload) =>
    request<AnnotationPayload & { id: number; roi_features: ROIFeatureDetail }>('/annotations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  annotations: (imageId: number) => request<AnnotationRecord[]>(`/images/${imageId}/annotations`),
  annotationFeatures: (annotationId: number) => request<ROIFeatureDetail>(`/annotations/${annotationId}/features`),
  createAnalysis: (payload: { patient_id: number; image_id?: number; annotation_id?: number; task_type?: string }) =>
    request<AnalysisTask>('/analysis/tasks', { method: 'POST', body: JSON.stringify(payload) }),
  analysisTasks: () => request<AnalysisTask[]>('/analysis/tasks'),
  analysisDetail: (taskId: number) => request<AnalysisDetail>(`/analysis/tasks/${taskId}/detail`),
  modelMetrics: () => request<ModelMetric[]>('/model/metrics'),
  featureImportance: () => request<FeatureImportance[]>('/model/feature-importance'),
  stats: () => request<StatsSummary>('/stats/summary'),
  audits: () => request<AuditRecord[]>('/audit/records'),
  updateAudit: (id: number, payload: Partial<AuditRecord>) =>
    request<AuditRecord>(`/audit/records/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  users: () => request<UserRecord[]>('/admin/users'),
  createUser: (payload: { username: string; password: string; name: string; role: string; department: string }) =>
    request<UserRecord>('/admin/users', { method: 'POST', body: JSON.stringify(payload) }),
  updateUser: (userId: number, payload: Partial<{ name: string; role: string; department: string; is_active: boolean; password: string }>) =>
    request<UserRecord>(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  downloadReport: async (taskId: number) => {
    const res = await fetch(`${API_BASE}/reports/tasks/${taskId}/export`, {
      headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    })
    if (!res.ok) throw new Error(`报告导出失败：${res.status}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis_task_${taskId}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  },
}
