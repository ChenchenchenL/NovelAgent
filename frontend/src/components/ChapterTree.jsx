import React from 'react'

export function ChapterTree({
  tree,
  project,
  selectedChapterId,
  selectedSceneId,
  onCreateVolume,
  onCreateChapter,
  onCreateScene,
  onSelectChapter,
  onSelectScene,
}) {
  const renderChapter = (ch) => (
    <div key={ch.id} className="tree-chapter">
      <div
        className={`chapter-item ${selectedChapterId === ch.id ? 'active' : ''}`}
        onClick={() => onSelectChapter(ch.id)}
      >
        <span className="chapter-item-name">第 {ch.sequence} 章 {ch.title}</span>
        <span className="badge">{ch.status}</span>
        <button
          className="mini-btn"
          onClick={(e) => {
            e.stopPropagation()
            onCreateScene(ch.id)
          }}
          title="新建场景"
        >
          + 场景
        </button>
      </div>
      {ch.scenes?.map((sc) => (
        <div
          key={sc.id}
          className={`tree-scene ${selectedSceneId === sc.id ? 'active' : ''}`}
          onClick={() => onSelectScene(sc.id)}
        >
          <span className="scene-item-name">{sc.sequence}. {sc.title}</span>
          <span className="badge-small">{sc.status}</span>
        </div>
      ))}
    </div>
  )

  return (
    <aside className="sidebar panel">
      <div className="panel-title">
        <span>篇章大纲</span>
        <div className="tree-top-actions">
          <button onClick={onCreateVolume} title="新建卷" disabled={!project}>
            + 卷
          </button>
          <button onClick={() => onCreateChapter(null)} title="新建未分卷章节" disabled={!project}>
            + 章
          </button>
        </div>
      </div>
      <div className="tree-container">
        {tree.volumes?.map((vol) => (
          <div key={vol.id} className="tree-volume">
            <div className="volume-header">
              <strong>第 {vol.sequence} 卷：{vol.title}</strong>
              <button className="mini-btn" onClick={() => onCreateChapter(vol.id)}>
                + 章
              </button>
            </div>
            {vol.chapters?.map(renderChapter)}
          </div>
        ))}

        {tree.unassigned_chapters?.length > 0 && (
          <div className="tree-volume">
            <div className="volume-header muted">未分卷章节</div>
            {tree.unassigned_chapters.map(renderChapter)}
          </div>
        )}
      </div>
    </aside>
  )
}
