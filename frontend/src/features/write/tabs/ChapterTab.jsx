import React from 'react'

export function ChapterTab({ selectedChapter, onChangeChapterStatus }) {
  if (!selectedChapter) {
    return (
      <div className="inspector-tab-content">
        <div className="empty-hint">在左侧大纲中点击章节，查看章节契约与状态流转</div>
      </div>
    )
  }

  return (
    <div className="inspector-tab-content chapter-tab">
      <div className="chapter-header-card">
        <div className="chapter-num">第 {selectedChapter.sequence} 章</div>
        <h4 className="chapter-title">{selectedChapter.title}</h4>
      </div>

      <div className="form-group-compact" style={{ marginTop: '12px' }}>
        <label>章节状态机流转</label>
        <select
          value={selectedChapter.status}
          onChange={(e) => onChangeChapterStatus(selectedChapter.id, e.target.value)}
        >
          <option value="IDEA">构思中 (IDEA)</option>
          <option value="OUTLINED">大纲已就绪 (OUTLINED)</option>
          <option value="IN_PROGRESS">正文创作中 (IN_PROGRESS)</option>
          <option value="READY_FOR_REVIEW">待审校 (READY_FOR_REVIEW)</option>
          <option value="RELEASED">已发布 (RELEASED)</option>
          <option value="LOCALLY_STALE">依赖已陈旧 (LOCALLY_STALE)</option>
        </select>
      </div>

      <div className="form-group-compact" style={{ marginTop: '12px' }}>
        <label>章节目标契约 (ChapterContract)</label>
        <pre className="code-box-compact">
          {JSON.stringify(selectedChapter.contract || { goal: '尚未设置章节全局目标' }, null, 2)}
        </pre>
      </div>
    </div>
  )
}
