export type AppRole = '医生' | '科室管理员' | '系统管理员'

export const routeRoles = {
  dashboard: ['医生', '科室管理员', '系统管理员'],
  patients: ['医生', '科室管理员'],
  imaging: ['医生', '科室管理员'],
  analysis: ['医生', '科室管理员'],
  audit: ['科室管理员'],
  users: ['系统管理员'],
} satisfies Record<string, AppRole[]>

export const roleProfiles: Record<AppRole, { title: string; scope: string; limits: string }> = {
  医生: {
    title: '医生工作台',
    scope: '患者建档、临床病理录入、MRI影像上传、ROI标注、pCR辅助分析发起',
    limits: '不能审核他人数据，不能管理用户账号',
  },
  科室管理员: {
    title: '科室质控工作台',
    scope: '审核医生提交的数据与标注结果，查看科室统计和可视化结果',
    limits: '不直接录入患者、上传影像或发起新的分析任务',
  },
  系统管理员: {
    title: '系统管理工作台',
    scope: '创建、禁用和分配医生/科室管理员/系统管理员账号权限',
    limits: '不参与患者业务数据录入、标注、分析或科室审核',
  },
}

export function currentUserRole(): AppRole | undefined {
  try {
    const role = JSON.parse(localStorage.getItem('pcr_user') || '{}').role
    return typeof role === 'string' && role in roleProfiles ? (role as AppRole) : undefined
  } catch {
    return undefined
  }
}

export function isDoctorRole(role?: string): role is '医生' {
  return role === '医生'
}
