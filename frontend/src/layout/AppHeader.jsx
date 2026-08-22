import React from 'react'

export function AppHeader({
  projectName,
  currentPath,
  selectedSceneTitle,
  onOpenSettings,
  onQuickSave,
  canSave,
  isSaving,
}) {
  const dirName = currentPath ? currentPath.split('/').pop() || currentPath : '未选择目录'

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="project-badge" title={`创作目录: ${currentPath || '未绑定'}`}>
          <span className="project-name">{projectName || '未命名小说项目'}</span>
          <span className="project-path-tag">{dirName}</span>
        </div>
        {selectedSceneTitle && (
          <div className="header-scene-pill">
            <span className="pill-dot"></span>
            <span className="pill-text">{selectedSceneTitle}</span>
          </div>
        )}
      </div>

      <div className="header-center">
        <div className="header-status-indicator">
          {isSaving ? (
            <span className="status-saving-badge">同步中...</span>
          ) : (
            <span className="status-ready-badge">正典一致</span>
          )}
        </div>
      </div>

      <div className="header-right">
        {canSave && (
          <button
            className="btn-header-action primary"
            onClick={onQuickSave}
            disabled={isSaving}
            title="将当前草稿采纳为不可变正典版本"
          >
            {isSaving ? '提交中...' : '提交正典'}
          </button>
        )}
        <button
          className="btn-header-icon"
          onClick={onOpenSettings}
          title="系统配置"
        >
          设置
        </button>
      </div>
    </header>
  )
}
