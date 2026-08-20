import React from 'react'

export function RevisionHistory({ revisions, onViewRevision, onDiffRevision }) {
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
          <div className="revision-actions">
            <button onClick={() => onViewRevision(rev.id)}>预览正文</button>
            {rev.base_revision_id && onDiffRevision && (
              <button onClick={() => onDiffRevision(rev.id, rev.base_revision_id)}>
                查看差异
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
