import React, { useState } from 'react'
import { AutoPlanModal } from '../agent/AutoPlanModal'

export function HomeView({
  currentPath,
  setCurrentPath,
  onOpenProject,
  onRefreshTree,
  projectOpened,
  onViewChange,
}) {
  const [showPlan, setShowPlan] = useState(false)
  const [notice, setNotice] = useState('')

  const handleOpen = async () => {
    if (!currentPath.trim()) return
    try {
      await onOpenProject()
      onViewChange('write')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handlePlanCompleted = async () => {
    await onRefreshTree()
    setShowPlan(false)
    onViewChange('write')
  }

  return (
    <div className="home-container" style={{ maxWidth: 640, margin: '60px auto', padding: '0 24px' }}>
      <div className="home-header" style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px' }}>NovelAgent 小说创作工作台</h1>
        <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
          面向长篇小说创作的架构级辅助系统。整合大纲推演、正典连续性约束、7维时空自检与分级模型网关。
        </p>
      </div>

      <div className="continuity-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <h4 style={{ fontSize: '14px', marginBottom: '12px', color: '#cbd5e1' }}>项目存储目录绑定</h4>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input
            type="text"
            value={currentPath}
            onChange={(e) => setCurrentPath(e.target.value)}
            placeholder="本地存储目录绝对路径 (如 /home/user/my_novel)"
            style={{ flex: 1 }}
          />
          <button className="btn-primary" onClick={handleOpen}>
            打开或初始化
          </button>
        </div>
        {notice && <p style={{ color: '#f87171', fontSize: '12.5px', marginTop: '6px' }}>{notice}</p>}
        {projectOpened && (
          <div style={{ marginTop: '8px', fontSize: '12.5px', color: '#10b981' }}>
            已授权并绑定项目目录：{currentPath}
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div className="tool-card">
          <div className="tool-badge-label">全书规划</div>
          <h4>全自动世界观与大纲推演</h4>
          <p>输入故事核心创意与题材，自动生成全书分卷、章节、初始人物档案与剧情线契约。</p>
          <button
            className="btn-primary"
            onClick={() => setShowPlan(true)}
            disabled={!projectOpened}
          >
            启动大纲推演
          </button>
        </div>

        <div className="tool-card">
          <div className="tool-badge-label">写作工作台</div>
          <h4>进入正文草稿与推演</h4>
          <p>打开三栏创作台，支持 Markdown 草稿写作、实时 7 维连续性自检与逆向正典抽取。</p>
          <button
            className="btn-primary"
            onClick={() => onViewChange('write')}
            disabled={!projectOpened}
          >
            进入创作空间
          </button>
        </div>
      </div>

      <AutoPlanModal
        isOpen={showPlan}
        onClose={() => setShowPlan(false)}
        onPlanCompleted={handlePlanCompleted}
      />
    </div>
  )
}
