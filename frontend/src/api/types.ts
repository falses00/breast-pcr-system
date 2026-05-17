export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserRecord
}

export interface UserRecord {
  id: number
  username: string
  name: string
  role: '医生' | '科室管理员' | '系统管理员'
  department: string
  is_active?: boolean
}

export interface Patient {
  id: number
  patient_code: string
  name_masked: string
  age: number
  gender: string
  visit_no?: string
  contact_masked?: string
  status?: string
  latest_clinical?: ClinicalRecord | null
}

export interface ClinicalRecord {
  id: number
  patient_id: number
  tumor_type: string
  hr_status?: string
  er_status: string
  pr_status: string
  her2_status: string
  nottingham_grade?: string | null
  menopause?: string | null
  ethnicity?: string | null
  mastectomy_post_nac?: boolean | null
  ki67?: number
  treatment_plan?: string
  pcr_label?: boolean | null
}

export interface ImageRecord {
  id: number
  patient_id: number
  filename: string
  file_uri: string
  image_url: string
  file_format: string
  status: string
  source_type?: string
}

export interface ROIFeatureDetail {
  id: number
  annotation_id: number
  area: number
  gray_mean: number
  gray_std: number
  gray_min: number
  gray_max: number
  gray_skewness: number
  gray_kurtosis: number
  gray_entropy: number
  gray_contrast: number
  gray_energy: number
  perimeter: number
  compactness: number
  circularity: number
}

export interface AnnotationPayload {
  patient_id: number
  image_id: number
  slice_no: number
  roi_json: { type: 'rectangle' | 'ellipse' | 'polygon'; points: Array<{ x: number; y: number }> }
  lesion_type: string
  remark?: string
}

export interface AnnotationRecord extends AnnotationPayload {
  id: number
  version_no: number
  roi_features?: ROIFeatureDetail
}

export interface AnalysisTask {
  id: number
  patient_id: number
  image_id?: number
  annotation_id?: number
  task_type: string
  task_status: string
  pcr_probability: number
  explanations: string[]
  risk_level?: string
  molecular_subtype?: string
  key_factors?: string[]
  disclaimer: string
  created_at: string
}

export interface AnalysisDetail extends AnalysisTask {
  patient?: {
    id: number
    patient_code: string
    name_masked: string
    age: number
    gender: string
  } | null
  clinical?: {
    tumor_type: string
    hr_status: string
    er_status: string
    pr_status: string
    her2_status: string
    nottingham_grade?: string | null
    menopause?: string | null
    ki67?: number
    treatment_plan?: string
    pcr_label?: boolean | null
  } | null
  image?: ImageRecord | null
  roi_features?: ROIFeatureDetail | null
}

export interface StatsSummary {
  patient_count: number
  image_count: number
  annotation_count: number
  task_count: number
  pcr_ratio: number | null
  pcr_positive_count: number
  pcr_negative_count: number
  age_distribution: Array<{ name: string; value: number }>
  tumor_type_distribution: Array<{ name: string; value: number }>
  er_pr_her2_pcr_relation: Array<{ name: string; value: number }>
  subtype_pcr_stats: Array<{ subtype: string; pcr: number; non_pcr: number; total: number }>
  lesion_area_distribution: number[]
  model_task_probabilities: number[]
  disclaimer: string
}

export interface AuditRecord {
  id: number
  biz_type: string
  biz_id: number
  review_status: string
  review_opinion?: string
  reviewer_id?: number
}

export interface ModelMetric {
  model_name: string
  data_source?: string
  task_kind?: string
  sample_count?: number | null
  test_count?: number | null
  accuracy: number
  precision: number
  recall: number
  f1: number
  auc: number
  confusion_matrix: number[][]
  disclaimer?: string
  source_url?: string
}

export interface FeatureImportance {
  model_name: string
  features: Array<{ name: string; importance: number }>
}
