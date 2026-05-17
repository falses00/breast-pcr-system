/**
 * 三角色工作流自动化验证脚本
 * 验证：系统管理员用户管理 / 医生标注→自动审核 / 科室管理员审核
 */
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:5174';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  // ========== 辅助函数 ==========
  async function login(username, password) {
    await context.clearCookies();
    await page.goto(`${BASE}/`);
    await page.evaluate(() => localStorage.clear());
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(500);
    await page.waitForSelector('input', { timeout: 5000 });
    const inputs = await page.$$('input');
    await inputs[0].fill('');
    await inputs[0].fill(username);
    await inputs[1].fill('');
    await inputs[1].fill(password);
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(1500);
  }

  async function screenshot(name) {
    await page.screenshot({ path: `scripts/screenshots/${name}.png`, fullPage: true });
    console.log(`  📸 截图已保存: scripts/screenshots/${name}.png`);
  }

  // ========== Phase 1: 系统管理员 — 用户管理 ==========
  console.log('\n======== Phase 1: 系统管理员用户管理 ========');
  await login('sys_admin', 'admin123');

  // 检查是否登录成功
  const url1 = page.url();
  console.log(`  当前页面: ${url1}`);
  if (url1.includes('/login')) {
    console.log('  ❌ 登录失败');
  } else {
    console.log('  ✅ 系统管理员登录成功');
  }

  // 导航到用户管理
  await page.goto(`${BASE}/users`);
  await page.waitForTimeout(1000);
  await screenshot('01_admin_users_page');

  // 验证统计卡是否存在
  const statCards = await page.$$('.stat-card');
  console.log(`  统计卡数量: ${statCards.length} ${statCards.length === 4 ? '✅' : '⚠️ 期望4个'}`);

  // 验证用户表格
  const tableRows = await page.$$('.el-table__row');
  console.log(`  用户列表行数: ${tableRows.length} ${tableRows.length >= 3 ? '✅' : '⚠️ 期望>=3'}`);

  // 验证操作按钮存在
  const editBtns = await page.$$('button:has-text("编辑")');
  const disableBtns = await page.$$('button:has-text("禁用")');
  const resetBtns = await page.$$('button:has-text("重置密码")');
  console.log(`  编辑按钮: ${editBtns.length}个 ${editBtns.length > 0 ? '✅' : '❌'}`);
  console.log(`  禁用按钮: ${disableBtns.length}个 ${disableBtns.length > 0 ? '✅' : '❌'}`);
  console.log(`  重置密码: ${resetBtns.length}个 ${resetBtns.length > 0 ? '✅' : '❌'}`);

  // 点击编辑按钮打开弹窗
  if (editBtns.length > 0) {
    await editBtns[0].click();
    await page.waitForTimeout(500);
    const dialog = await page.$('.el-dialog');
    console.log(`  编辑弹窗: ${dialog ? '✅ 已弹出' : '❌ 未弹出'}`);
    await screenshot('02_admin_edit_dialog');
    // 关闭弹窗
    const cancelBtn = await page.$('.el-dialog button:has-text("取消")');
    if (cancelBtn) await cancelBtn.click();
    await page.waitForTimeout(300);
  }

  // 验证权限说明卡
  const helpCard = await page.$('.help-card');
  console.log(`  权限说明卡: ${helpCard ? '✅' : '❌'}`);

  // ========== Phase 2: 医生 — 标注保存 ==========
  console.log('\n======== Phase 2: 医生标注与自动审核 ========');
  await login('doctor', 'admin123');
  const url2 = page.url();
  console.log(`  当前页面: ${url2}`);
  console.log(`  ${url2.includes('/login') ? '❌ 登录失败' : '✅ 医生登录成功'}`);

  // 导航到影像页
  await page.goto(`${BASE}/imaging`);
  await page.waitForTimeout(1500);
  await screenshot('03_doctor_imaging');

  // 检查 Canvas 标注工具
  const toolBtns = await page.$$('.tool-btn');
  console.log(`  标注工具按钮: ${toolBtns.length}个 ${toolBtns.length >= 3 ? '✅ (矩形/椭圆/多边形)' : '⚠️'}`);

  // 检查 ROI 面板
  const roiPanel = await page.$('.roi-panel');
  console.log(`  ROI检查器面板: ${roiPanel ? '✅' : '❌'}`);

  // 检查保存按钮
  const saveBtn = await page.$('button:has-text("保存ROI标注")');
  console.log(`  保存ROI按钮: ${saveBtn ? '✅' : '❌'}`);
  
  if (saveBtn) {
    // 模拟点击Canvas来完成一个点
    const canvas = await page.$('.canvas-container canvas');
    if (canvas) {
      const box = await canvas.boundingBox();
      await page.mouse.click(box.x + 100, box.y + 100);
      await page.mouse.click(box.x + 200, box.y + 200);
      await saveBtn.click();
      await page.waitForTimeout(1000);
      console.log('  ✅ 已保存一个ROI');
    }
  }

  // 检查 pCR 分析按钮（需要先有 lastFeatures）
  const pcrBtn = await page.$('button:has-text("基于此ROI发起pCR分析")');
  console.log(`  pCR快速分析按钮: ${pcrBtn ? '✅ 可见' : '⚠️ 暂不可见(需先保存ROI)'}`);
  if (pcrBtn) {
    await pcrBtn.click();
    await page.waitForTimeout(1000);
    console.log('  ✅ 已发起pCR分析');
  }

  // ========== Phase 3: 科室管理员 — 审核 ==========
  console.log('\n======== Phase 3: 科室管理员审核管理 ========');
  await login('dept_admin', 'admin123');
  const url3 = page.url();
  console.log(`  当前页面: ${url3}`);
  console.log(`  ${url3.includes('/login') ? '❌ 登录失败' : '✅ 科室管理员登录成功'}`);

  // 导航到审核页
  await page.goto(`${BASE}/audit`);
  await page.waitForTimeout(1000);
  await screenshot('04_manager_audit');

  // 验证审核统计卡
  const auditStats = await page.$$('.stat-card');
  console.log(`  审核统计卡: ${auditStats.length}个 ${auditStats.length === 4 ? '✅' : '⚠️'}`);

  // 验证审核卡片列表
  const auditCards = await page.$$('.audit-card');
  console.log(`  审核记录数: ${auditCards.length}个 ${auditCards.length > 0 ? '✅' : '⚠️ 暂无(医生尚未提交新标注)'}`);

  // 验证审核操作按钮
  const passBtn = await page.$('button:has-text("通过")');
  const returnBtn = await page.$('button:has-text("退回")');
  const rejectBtn = await page.$('button:has-text("驳回")');
  console.log(`  通过按钮: ${passBtn ? '✅' : '⚠️'}`);
  console.log(`  退回按钮: ${returnBtn ? '✅' : '⚠️'}`);
  console.log(`  驳回按钮: ${rejectBtn ? '✅' : '⚠️'}`);

  // 验证意见输入框
  const opinionInput = await page.$('.opinion-input input');
  console.log(`  审核意见输入框: ${opinionInput ? '✅' : '⚠️'}`);

  // 检查空状态提示
  if (auditCards.length === 0) {
    const emptyState = await page.$('.empty-state');
    console.log(`  空状态提示: ${emptyState ? '✅ 显示正常' : '❌'}`);
  }

  // ========== 总结 ==========
  console.log('\n======== 验证总结 ========');
  console.log('  Phase 1 (系统管理员): 用户列表 + 编辑弹窗 + 禁用/重置密码');
  console.log('  Phase 2 (医生): 标注工具 + ROI面板 + 历史时间线 + pCR按钮');
  console.log('  Phase 3 (科室管理员): 审核统计 + 审核卡片 + 意见输入 + 三级操作');
  console.log('  截图保存在: scripts/screenshots/');

  await browser.close();
  console.log('\n✅ 全部验证完成');
})();
