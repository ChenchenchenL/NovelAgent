import React from 'react'

export function ConflictDialog({ conflict, onReloadCanon, onKeepDraft, onCancel }) {
  if (!conflict) return null

  return (
    <div className="conflict-modal-backdrop">
      <div className="conflict-modal-card">
        <h4>检测到正典版本冲突</h4>
        <p className="conflict-desc">
          当前场景的正典版本已更新为 #{conflict.current_revision_id || '最新'}，
          您的工作区草稿基于版本 #{conflict.workspace_base_revision_id || '旧版'}。
        </p>
        <div className="conflict-actions">
          <button className="primary" onClick={onReloadCanon}>
            以最新正典为准（重新加载）
          </button>
          <button onClick={onKeepDraft}>
            保留当前草稿（另存为补丁）
          </button>
          <button onClick={onCancel}>
            取消
          </button>
        </div>
      </div>
    </div>
  )
}
