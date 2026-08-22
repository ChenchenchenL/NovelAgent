import React from 'react'

export function SceneBreadcrumb({
  scene,
  activeTab,
  onTabChange,
  draftContent = '',
  revisionsCount = 0,
  onSaveScene,
  busy,
  viewingRevision,
}) {
  const wordCount = draftContent.replace(/\s+/g, '').length

  return (
    <div className="scene-breadcrumb-bar">
      <div className="breadcrumb-left">
        <strong className="scene-title-text">{scene?.title || '未选择章节场景'}</strong>
        <span className="word-count-badge">{wordCount} 字</span>
      </div>

      <div className="breadcrumb-center-tabs">
        <button
          className={`breadcrumb-tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onTabChange('editor')}
        >
          正文编辑
        </button>
        <button
          className={`breadcrumb-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => onTabChange('preview')}
        >
          排版阅读
        </button>
        <button
          className={`breadcrumb-tab ${activeTab === 'revisions' ? 'active' : ''}`}
          onClick={() => onTabChange('revisions')}
          disabled={!scene}
        >
          历史版本 ({revisionsCount})
        </button>
      </div>

      <div className="breadcrumb-right">
        <button
          className="btn-sm btn-blue"
          onClick={onSaveScene}
          disabled={!scene || busy || Boolean(viewingRevision)}
          title="将草稿保存为正典版本"
        >
          {busy ? '保存中...' : '保存正典'}
        </button>
      </div>
    </div>
  )
}
