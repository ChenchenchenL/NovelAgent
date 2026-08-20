import React from 'react'

export function ChapterControl({ selectedChapter, onChangeStatus }) {
  return (
    <aside className="review panel">
      <div className="panel-title">
        <span>章节控制</span>
        <span className="muted">{selectedChapter ? `第 ${selectedChapter.sequence} 章` : '未选'}</span>
      </div>
      {selectedChapter ? (
        <div className="chapter-control-panel">
          <h4>{selectedChapter.title}</h4>
          <div className="field-group">
            <label>章节状态机流转</label>
            <select
              value={selectedChapter.status}
              onChange={(e) => onChangeStatus(selectedChapter.id, e.target.value)}
            >
              <option value="IDEA">IDEA</option>
              <option value="OUTLINED">OUTLINED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="READY_FOR_REVIEW">READY_FOR_REVIEW</option>
              <option value="RELEASED">RELEASED</option>
              <option value="LOCALLY_STALE">LOCALLY_STALE</option>
            </select>
          </div>
          <div className="field-group">
            <label>ChapterContract</label>
            <pre className="code-box">
              {JSON.stringify(selectedChapter.contract || { goal: '尚未规划章节契约' }, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <p className="empty">在左侧选择章节查看详细状态与契约。</p>
      )}
    </aside>
  )
}
