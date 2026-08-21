import React from 'react'

export function Topbar({ notice, onToggleModelConfig, showModelConfig }) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">LOCAL CANON & AI AGENT ENGINE</span>
        <h1>NovelAgent</h1>
      </div>
      <div className="topbar-right">
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
