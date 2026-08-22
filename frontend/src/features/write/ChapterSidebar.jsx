import React from 'react'

export function ChapterSidebar({
  tree,
  project,
  selectedChapterId,
  selectedSceneId,
  onCreateVolume,
  onCreateChapter,
  onCreateScene,
  onSelectChapter,
  onSelectScene,
  onOpenAutoPlan,
}) {
  const totalChapters = (tree?.volumes?.reduce((acc, v) => acc + (v.chapters?.length || 0), 0) || 0) + (tree?.unassigned_chapters?.length || 0)

  return (
    <aside className="chapter-sidebar">
      <div className="sidebar-header">
        <span>目录 ({totalChapters} 章)</span>
        <div className="tree-actions">
          <button className="mini-btn" onClick={onCreateVolume} title="新增卷">+ 卷</button>
          <button className="mini-btn" onClick={() => onCreateChapter(null)} title="新增章节">+ 章</button>
        </div>
      </div>

      <div className="tree-scroll-area">
        {!project ? (
          <div className="empty-hint">请先打开或绑定小说项目文件夹</div>
        ) : (
          <>
            {tree?.volumes?.map((vol) => (
              <div key={vol.id} className="tree-volume-group">
                <div className="volume-label">
                  <span>{vol.title}</span>
                  <button className="mini-btn" onClick={() => onCreateChapter(vol.id)}>+ 章</button>
                </div>
                <div className="tree-chapter-group">
                  {vol.chapters?.map((ch) => (
                    <div key={ch.id}>
                      <div
                        className={`chapter-row ${selectedChapterId === ch.id ? 'active' : ''}`}
                        onClick={() => onSelectChapter(ch.id)}
                      >
                        <span>{ch.title}</span>
                        <button className="mini-btn" onClick={(e) => { e.stopPropagation(); onCreateScene(ch.id) }}>+ 节</button>
                      </div>
                      {ch.scenes?.map((sc) => (
                        <div
                          key={sc.id}
                          className={`scene-row ${selectedSceneId === sc.id ? 'active' : ''}`}
                          onClick={() => onSelectScene(sc.id)}
                        >
                          <span>{sc.sequence ? `${sc.sequence}. ` : ''}{sc.title}</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {tree?.unassigned_chapters?.map((ch) => (
              <div key={ch.id} className="tree-chapter-group">
                <div
                  className={`chapter-row ${selectedChapterId === ch.id ? 'active' : ''}`}
                  onClick={() => onSelectChapter(ch.id)}
                >
                  <span>{ch.title}</span>
                  <button className="mini-btn" onClick={(e) => { e.stopPropagation(); onCreateScene(ch.id) }}>+ 节</button>
                </div>
                {ch.scenes?.map((sc) => (
                  <div
                    key={sc.id}
                    className={`scene-row ${selectedSceneId === sc.id ? 'active' : ''}`}
                    onClick={() => onSelectScene(sc.id)}
                  >
                    <span>{sc.sequence ? `${sc.sequence}. ` : ''}{sc.title}</span>
                  </div>
                ))}
              </div>
            ))}
          </>
        )}
      </div>

      <div className="sidebar-bottom-actions">
        <button className="btn-small btn-blue" onClick={onOpenAutoPlan}>
          全书大纲与设定推演
        </button>
      </div>
    </aside>
  )
}
