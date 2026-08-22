import React from 'react'

export const VIEWS = {
  WRITE: 'write',
  PLAN: 'plan',
  CODEX: 'codex',
  SEARCH: 'search',
  QUALITY: 'quality',
  GLOBAL: 'global',
  SETTINGS: 'settings',
}

export function ActivityBar({ activeView, onViewChange }) {
  const navItems = [
    { id: VIEWS.WRITE, code: 'WR', label: '正文写作' },
    { id: VIEWS.PLAN, code: 'PL', label: '大纲剧情' },
    { id: VIEWS.CODEX, code: 'CX', label: '设定正典' },
    { id: VIEWS.SEARCH, code: 'SR', label: '检索图谱' },
    { id: VIEWS.QUALITY, code: 'QC', label: '质量风控' },
    { id: VIEWS.GLOBAL, code: 'GL', label: '全局智能' },
  ]

  return (
    <nav className="activity-bar" aria-label="工作区导航">
      <div className="activity-bar-brand" title="NovelAgent">
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
          title="系统配置与工具箱"
        >
          <span className="activity-code-badge">ST</span>
          <span className="activity-label">设置工具</span>
        </button>
      </div>
    </nav>
  )
}
