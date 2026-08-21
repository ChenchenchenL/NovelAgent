import React, { useState } from 'react'

export function ConflictResolutionDialog({ conflict, onClose, onResolve }) {
  const [selectedOption, setSelectedOption] = useState(0)

  if (!conflict) return null

  const handleApply = () => {
    const option = conflict.resolution_options?.[selectedOption] || '文学留白'
    onResolve(conflict.id, option)
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content conflict-resolution-modal">
        <div className="conflict-dialog-header">
          <h3>
            <span className="conflict-badge-blocking">硬冲突检测</span>
            {conflict.severity || 'BLOCKING_CONFIRMED'}
          </h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="conflict-dialog-body">
          <p className="conflict-message"><strong>冲突说明：</strong>{conflict.message}</p>

          <div className="conflict-claims-comparison">
            {conflict.left_claim && (
              <div className="claim-box left-claim">
                <div className="box-title">左侧正典事实 #{conflict.left_claim.id}</div>
                <div className="triple-row">
                  <span>主体: <strong>{conflict.left_claim.subject}</strong></span>
                  <span>谓词: <code>{conflict.left_claim.predicate}</code></span>
                  <span>客体: <strong>{conflict.left_claim.object_value}</strong></span>
                </div>
              </div>
            )}

            {conflict.right_claim && (
              <div className="claim-box right-claim">
                <div className="box-title">右侧正典事实 #{conflict.right_claim.id}</div>
                <div className="triple-row">
                  <span>主体: <strong>{conflict.right_claim.subject}</strong></span>
                  <span>谓词: <code>{conflict.right_claim.predicate}</code></span>
                  <span>客体: <strong>{conflict.right_claim.object_value}</strong></span>
                </div>
              </div>
            )}
          </div>

          <div className="resolution-options-box">
            <label>推荐解决策略：</label>
            <div className="options-list">
              {(conflict.resolution_options || ['修改冲突主张', '标记为文学留白']).map((opt, idx) => (
                <label key={idx} className={`option-item ${selectedOption === idx ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="resolution_option"
                    checked={selectedOption === idx}
                    onChange={() => setSelectedOption(idx)}
                  />
                  <span>{opt}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="conflict-dialog-footer">
          <button className="btn-secondary" onClick={onClose}>取消</button>
          <button className="btn-primary" onClick={handleApply}>应用裁决方案</button>
        </div>
      </div>
    </div>
  )
}
