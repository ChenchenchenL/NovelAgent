import React from 'react'

export function Topbar({
  projectName,
  scene,
  onOpenModelConfig,
  onOpenContinuity,
  onOpenPlot,
  onOpenSearch,
  onOpenQuality,
  onOpenGlobal,
  onOpenImport,
  onOpenFsck,
  onOpenBackup,
  onSaveScene,
  busy,
}) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="brand">NovelAgent</span>
        <span className="project-tag">{projectName || '未打开项目'}</span>
        {scene && <span className="scene-tag">当前：{scene.title}</span>}
      </div>

      <div className="topbar-actions">
        <button onClick={onOpenPlot}>大纲剧情</button>
        <button onClick={onOpenContinuity}>设定正典</button>
        <button onClick={onOpenSearch}>检索图谱</button>
        <button onClick={onOpenQuality}>文本风控</button>
        <button onClick={onOpenGlobal}>全局智能</button>
        <button onClick={onOpenImport}>存量导入</button>
        <button onClick={onOpenFsck}>一致性检查</button>
        <button onClick={onOpenBackup}>备份导出</button>
        <button onClick={onOpenModelConfig}>模型设置</button>

        {scene && (
          <button
            className="primary"
            onClick={onSaveScene}
            disabled={busy}
            title="将工作区草稿保存为不可变版本并采纳为正典"
          >
            {busy ? '采纳中...' : '提交正典'}
          </button>
        )}
      </div>
    </header>
  )
}
