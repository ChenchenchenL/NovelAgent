import React from 'react'

export function SceneBreadcrumb({
  scene,
  activeTab,
  onTabChange,
  revisionsCount,
  onChangeSceneStatus,
  onSaveScene,
  busy,
  viewingRevision,
}) {
  return (
    <div className="scene-breadcrumb-bar">
      <div className="breadcrumb-left">
        <strong className="scene-title-text">{scene?.title || '未选择场景'}</strong>
        {scene && (
          <div className="scene-meta-badges">
            <span className="meta-badge">POV: {scene.pov || '未设'}</span>
            <span className="meta-badge">地点: {scene.location || '未设'}</span>
            <select
              className="scene-status-dropdown"
              value={scene.status}
              onChange={(e) => onChangeSceneStatus(scene.id, e.target.value)}
            >
              <option value="PLANNED">规划中 (PLANNED)</option>
              <option value="WRITING">起草中 (WRITING)</option>
              <option value="PARTIALLY_ACCEPTED">部分采纳 (PARTIALLY_ACCEPTED)</option>
              <option value="EXTRACTION_PENDING">待抽取 (EXTRACTION_PENDING)</option>
              <option value="SCENE_ACCEPTED">正典已确认 (SCENE_ACCEPTED)</option>
            </select>
          </div>
        )}
      </div>

      <div className="breadcrumb-center-tabs">
        <button
          className={`breadcrumb-tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onTabChange('editor')}
        >
          草稿编辑
        </button>
        <button
          className={`breadcrumb-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => onTabChange('preview')}
        >
          排版预览
        </button>
        <button
          className={`breadcrumb-tab ${activeTab === 'arbitration' ? 'active' : ''}`}
          onClick={() => onTabChange('arbitration')}
          disabled={!scene}
        >
          正典抽取与仲裁
        </button>
        <button
          className={`breadcrumb-tab ${activeTab === 'revisions' ? 'active' : ''}`}
          onClick={() => onTabChange('revisions')}
          disabled={!scene}
        >
          版本历史 ({revisionsCount || 0})
        </button>
      </div>

      <div className="breadcrumb-right">
        <button
          className="btn-save-canon"
          onClick={onSaveScene}
          disabled={!scene || busy || Boolean(viewingRevision)}
          title="将草稿采纳为正典"
        >
          {busy ? '提交中...' : '提交为正典'}
        </button>
      </div>
    </div>
  )
}
