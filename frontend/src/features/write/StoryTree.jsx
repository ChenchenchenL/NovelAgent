import React from 'react'

/**
 * Simplified story outline tree.
 * Shows: Volume > Chapter > Scene.
 * Removes status badges (PLANNED/WRITING etc.) — those are AI-managed internals.
 */
export function StoryTree({
  tree,
  project,
  selectedSceneId,
  onSelectScene,
  onCreateVolume,
  onCreateChapter,
  onCreateScene,
}) {
  if (!project || !tree) {
    return (
      <aside className="sidebar panel">
        <div className="panel-title">故事结构</div>
        <div style={{ padding: '16px', color: '#64748b', fontSize: '13px' }}>
          打开项目后，AI 会自动生成故事结构。
        </div>
      </aside>
    )
  }

  const renderScene = (sc) => (
    <div
      key={sc.id}
      className={`tree-scene ${selectedSceneId === sc.id ? 'active' : ''}`}
      onClick={() => onSelectScene(sc.id)}
      style={{ paddingLeft: '24px' }}
    >
      <span className="scene-item-name">{sc.sequence}. {sc.title}</span>
    </div>
  )

  const renderChapter = (ch) => (
    <div key={ch.id} className="tree-chapter">
      <div className="chapter-item">
        <span className="chapter-item-name">{ch.title}</span>
        <button
          className="mini-btn"
          onClick={(e) => { e.stopPropagation(); onCreateScene(ch.id) }}
          title="新增场景"
        >＋</button>
      </div>
      {ch.scenes?.map(renderScene)}
    </div>
  )

  return (
    <aside className="sidebar panel">
      <div className="panel-title">
        <span>故事结构</span>
        <div className="tree-top-actions">
          <button onClick={onCreateVolume} title="新增卷" disabled={!project}>＋卷</button>
          <button onClick={() => onCreateChapter(null)} title="新增章节" disabled={!project}>＋章</button>
        </div>
      </div>
      <div className="tree-container">
        {tree.volumes?.map((vol) => (
          <div key={vol.id} className="tree-volume">
            <div className="volume-header">
              <strong>{vol.title}</strong>
              <button className="mini-btn" onClick={() => onCreateChapter(vol.id)}>＋章</button>
            </div>
            {vol.chapters?.map(renderChapter)}
          </div>
        ))}
        {tree.unassigned_chapters?.length > 0 && (
          <div className="tree-volume">
            <div className="volume-header muted">未分卷</div>
            {tree.unassigned_chapters.map(renderChapter)}
          </div>
        )}
      </div>
    </aside>
  )
}
