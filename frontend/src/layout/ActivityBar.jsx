import React from 'react'

export const VIEWS = {
  WRITE: 'write',
  PLAN: 'plan',
  CODEX: 'codex',
  SETTINGS: 'settings',
}

export function ActivityBar({ activeView, onViewChange }) {
  const navItems = [
    { id: VIEWS.WRITE, code: 'WR', label: '正文写作' },
    { id: VIEWS.PLAN, code: 'PL', label: '故事大纲' },
    { id: VIEWS.CODEX, code: 'CX', label: '人物设定' },
  ]

  return (
    <nav className="activity-bar" aria-label="创作导航">
      <div className="activity-bar-brand" title="NovelAgent 个人小说创作">
        <span className="brand-logo-text">NA</span>
      </div>
      <div className="activity-bar-main">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`activity-btn ${activeView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
            title={item.label}
          >
            <span className="activity-code-badge">{item.code}</span>
            <span className="activity-label">{item.label}</span>
          </button>
        ))}
      </div>
      <div className="activity-bar-bottom">
        <button
          className={`activity-btn ${activeView === VIEWS.SETTINGS ? 'active' : ''}`}
          onClick={() => onViewChange(VIEWS.SETTINGS)}
          title="项目与模型设置"
        >
          <span className="activity-code-badge">ST</span>
          <span className="activity-label">设置</span>
        </button>
      </div>
    </nav>
  )
}
