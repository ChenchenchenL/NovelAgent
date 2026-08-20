import React from 'react'

export function RevisionDiff({ diff, onClose }) {
  if (!diff) return null

  const lines = (diff.unified_diff || '').split('\n')

  return (
    <div className="diff-modal-backdrop">
      <div className="diff-modal-card">
        <div className="diff-header">
          <h4>版本差异对比 (对比基准: #{diff.base_revision_id || '无'} vs 目标: #{diff.target_revision_id})</h4>
          <div className="diff-stats">
            <span className="diff-add">+{diff.additions}</span>
            <span className="diff-del">-{diff.deletions}</span>
            <button onClick={onClose}>关闭</button>
          </div>
        </div>
        <div className="diff-content">
          {lines.map((line, idx) => {
            let type = 'normal'
            if (line.startsWith('+') && !line.startsWith('+++')) type = 'add'
            if (line.startsWith('-') && !line.startsWith('---')) type = 'del'
            if (line.startsWith('@@')) type = 'hunk'
            return (
              <div key={idx} className={`diff-line diff-${type}`}>
                {line || ' '}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
