import React from 'react'

export function AppHeader({
  projectName,
  currentPath,
  selectedSceneTitle,
  onOpenProjectSettings,
  onOpenOutlineModal,
  onOpenModelModal,
  onQuickSave,
  canSave,
  isSaving,
}) {
  const dirName = currentPath ? currentPath.split('/').pop() || currentPath : '未选择目录'

  return (
    <header className="app-header">
      <div className="header-left">
        <span className="brand-title">NovelAgent</span>
        <span className="header-divider">/</span>
        <div
          className="project-badge"
          onClick={onOpenProjectSettings}
          title={`点击切换小说目录 (当前: ${currentPath || '未绑定'})`}
        >
          <span>{projectName || '我的小说'}</span>
          <span className="project-path-tag">({dirName})</span>
        </div>
        {selectedSceneTitle && (
          <div className="header-scene-pill">
            <span className="pill-dot"></span>
            <span>{selectedSceneTitle}</span>
          </div>
        )}
      </div>

      <div className="header-center">
        <div className="header-status-indicator">
          {isSaving ? (
            <span className="status-saving-badge">正在自动保存...</span>
          ) : (
            <span className="status-ready-badge">正典已同步</span>
          )}
        </div>
      </div>

      <div className="header-right">
        <button className="btn-sm" onClick={onOpenOutlineModal} title="查看与调整全书大纲与设定">
          故事大纲与设定
        </button>
        <button className="btn-sm" onClick={onOpenModelModal} title="自定义配置 OpenAI / DeepSeek / Claude / 本地大模型">
          模型设置
        </button>
        <button className="btn-sm" onClick={onOpenProjectSettings} title="切换或新建小说项目文件夹">
          切换项目
        </button>
        {canSave && (
          <button
            className="btn-header-action btn-blue"
            onClick={onQuickSave}
            disabled={isSaving}
            title="保存当前正文为不可变正典版本"
          >
            {isSaving ? '保存中...' : '保存正典'}
          </button>
        )}
      </div>
    </header>
  )
}
