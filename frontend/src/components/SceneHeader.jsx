import React from 'react'
import { GenerationControl } from './GenerationControl'

export function SceneHeader({
  scene,
  tab,
  setTab,
  revisionsCount,
  busy,
  viewingRevision,
  generating,
  onChangeSceneStatus,
  onSave,
  onGenerate,
}) {
  return (
    <div className="panel-title">
      <div className="scene-meta">
        <strong>{scene?.title || '未选择场景'}</strong>
        {scene && (
          <div className="scene-tags">
            <span className="tag">POV: {scene.pov || '未设'}</span>
            <span className="tag">地点: {scene.location || '未设'}</span>
            <select className="status-select" value={scene.status} onChange={(e) => onChangeSceneStatus(scene.id, e.target.value)}>
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
        <GenerationControl onGenerate={onGenerate} generating={generating} disabled={!scene || Boolean(viewingRevision)} />
        <button className={tab === 'editor' ? 'primary' : ''} onClick={() => setTab('editor')}>编辑</button>
        <button className={tab === 'preview' ? 'primary' : ''} onClick={() => setTab('preview')}>预览</button>
        <button className={tab === 'arbitration' ? 'primary' : ''} onClick={() => setTab('arbitration')} disabled={!scene}>仲裁</button>
        <button className={tab === 'contracts' ? 'primary' : ''} onClick={() => setTab('contracts')} disabled={!scene}>契约</button>
        <button className={tab === 'revisions' ? 'primary' : ''} onClick={() => setTab('revisions')} disabled={!scene}>版本({revisionsCount})</button>
        <button className="primary" onClick={onSave} disabled={!scene || busy || Boolean(viewingRevision)}>采纳正典</button>
      </div>
    </div>
  )
}
