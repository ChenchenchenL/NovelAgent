import React from 'react'

export function Topbar({
  notice,
  showModelConfig,
  onToggleModelConfig,
  onOpenImport,
  onOpenFsck,
  onOpenBackup,
  onOpenContinuity,
  onOpenPlot,
  onOpenSearch,
  onOpenQuality,
  onOpenGlobal,
}) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">LOCAL CANON & AI AGENT ENGINE</span>
        <h1>NovelAgent</h1>
      </div>
      <div className="topbar-right">
        <button className="btn-small" onClick={onOpenGlobal}>
          🌐 全局智能与GraphRAG
        </button>
        <button className="btn-small" onClick={onOpenQuality}>
          🛡️ 质控与声音
        </button>
        <button className="btn-small" onClick={onOpenSearch}>
          🔎 检索与ContextPack
        </button>
        <button className="btn-small" onClick={onOpenPlot}>
          📈 剧情与影响图
        </button>
        <button className="btn-small" onClick={onOpenContinuity}>
          🎭 设定与连续性
        </button>
        <button className="btn-small" onClick={onOpenImport}>
          📦 存量导入
        </button>
        <button className="btn-small" onClick={onOpenFsck}>
          🩺 FSCK修复
        </button>
        <button className="btn-small" onClick={onOpenBackup}>
          💾 备份导出
        </button>
        <button
          className={`btn-small ${showModelConfig ? 'btn-active' : ''}`}
          onClick={onToggleModelConfig}
        >
          ⚙️ 模型设置
        </button>
        <span className="status">{notice}</span>
      </div>
    </header>
  )
}
