import React from 'react'
import { ContractPanel } from './ContractPanel'
import { RevisionHistory } from './RevisionHistory'

export function SceneEditor({
  scene,
  tab,
  setTab,
  viewingRevision,
  setViewingRevision,
  revisions,
  busy,
  onSceneContentChange,
  onChangeSceneStatus,
  onSaveScene,
  onViewRevision,
}) {
  return (
    <section className="editor panel">
      <div className="panel-title">
        <div className="scene-meta">
          <strong>{scene?.title || '未选择场景'}</strong>
          {scene && (
            <div className="scene-tags">
              <span className="tag">POV: {scene.pov || '未设'}</span>
              <span className="tag">地点: {scene.location || '未设'}</span>
              <select
                className="status-select"
                value={scene.status}
                onChange={(e) => onChangeSceneStatus(scene.id, e.target.value)}
              >
                <option value="PLANNED">PLANNED</option>
                <option value="WRITING">WRITING</option>
                <option value="PARTIALLY_ACCEPTED">PARTIALLY_ACCEPTED</option>
                <option value="EXTRACTION_PENDING">EXTRACTION_PENDING</option>
                <option value="SCENE_ACCEPTED">SCENE_ACCEPTED</option>
              </select>
            </div>
          )}
        </div>
        <div className="actions">
          <button
            className={tab === 'editor' ? 'primary' : ''}
            onClick={() => setTab('editor')}
          >
            正文编辑
          </button>
          <button
            className={tab === 'contracts' ? 'primary' : ''}
            onClick={() => setTab('contracts')}
            disabled={!scene}
          >
            契约与状态
          </button>
          <button
            className={tab === 'revisions' ? 'primary' : ''}
            onClick={() => setTab('revisions')}
            disabled={!scene}
          >
            版本历史 ({revisions.length})
          </button>
          <button
            className="primary"
            onClick={onSaveScene}
            disabled={!scene || busy || viewingRevision !== null}
          >
            采纳为正典版本
          </button>
        </div>
      </div>

      {tab === 'editor' && (
        <>
          {viewingRevision && (
            <div className="revision-banner">
              <span>
                正在预览历史版本 #{viewingRevision.id}（{viewingRevision.created_at}）
              </span>
              <button onClick={() => setViewingRevision(null)}>返回当前版本</button>
            </div>
          )}
          <textarea
            className="editor-area"
            value={viewingRevision ? viewingRevision.content : scene?.content || ''}
            disabled={!scene || viewingRevision !== null}
            onChange={(e) => onSceneContentChange(e.target.value)}
            placeholder="在左侧篇章树中选择场景开始创作..."
          />
        </>
      )}

      {tab === 'contracts' && <ContractPanel scene={scene} />}

      {tab === 'revisions' && (
        <RevisionHistory
          revisions={revisions}
          onViewRevision={onViewRevision}
        />
      )}
    </section>
  )
}
