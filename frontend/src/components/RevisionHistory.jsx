import React from 'react'

export function RevisionHistory({ revisions, onViewRevision }) {
  if (!revisions || revisions.length === 0) {
    return <p className="empty">暂无历史版本</p>
  }

  return (
    <div className="revisions-list">
      {revisions.map((rev) => (
        <div key={rev.id} className="revision-card">
          <div>
            <strong>版本 #{rev.id}</strong> ({rev.source}) · {rev.created_at}
            <div className="muted code-text">Hash: {rev.content_hash}</div>
          </div>
          <button onClick={() => onViewRevision(rev.id)}>预览正文</button>
        </div>
      ))}
    </div>
  )
}
