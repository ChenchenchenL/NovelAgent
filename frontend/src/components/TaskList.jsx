import React, { useState } from 'react'

export function TaskList({ runs = [] }) {
  const [expanded, setExpanded] = useState(false)

  if (!runs || runs.length === 0) return null

  return (
    <div className="task-list-container">
      <div className="task-list-header" onClick={() => setExpanded(!expanded)}>
        <span>生成历史记录 ({runs.length})</span>
        <span className="toggle-icon">{expanded ? '收起' : '展开'}</span>
      </div>

      {expanded && (
        <div className="task-list-body">
          {runs.map((run) => (
            <div key={run.id} className={`task-item task-status-${(run.status || '').toLowerCase()}`}>
              <div className="task-item-top">
                <span className="task-id">#{run.id}</span>
                <span className="task-type">{run.task_type || '生成'}</span>
                <span className={`status-badge badge-${(run.status || '').toLowerCase()}`}>
                  {run.status}
                </span>
              </div>
              <div className="task-item-meta">
                <span>Tier: {run.model_tier}</span>
                {run.actual_model && <span>模型: {run.actual_model}</span>}
                {run.token_usage?.total_tokens && (
                  <span>Token: {run.token_usage.total_tokens}</span>
                )}
              </div>
              {run.error_message && (
                <div className="task-item-error">{run.error_message}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
