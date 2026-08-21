import React from 'react'

export function CandidateCard({ candidate, isSelected, onSelect, onDecide }) {
  const modClass = `modality-${(candidate.modality || '').toLowerCase()}`
  const statusClass = `status-${(candidate.status || '').toLowerCase()}`

  return (
    <div
      className={`candidate-card ${isSelected ? 'selected' : ''} ${statusClass}`}
      onClick={() => onSelect(candidate)}
    >
      <div className="candidate-card-top">
        <span className={`modality-badge ${modClass}`}>{candidate.modality}</span>
        <span className="confidence-tag">置信度 {Math.round((candidate.confidence || 0) * 100)}%</span>
        <span className={`claim-status-pill ${statusClass}`}>{candidate.status}</span>
      </div>

      <div className="candidate-triple">
        <strong className="triple-subject">{candidate.subject}</strong>
        <span className="triple-predicate">[{candidate.predicate}]</span>
        <span className="triple-object">{candidate.object_value}</span>
      </div>

      {candidate.cognitive_subject && (
        <div className="cognitive-note">认知主体: {candidate.cognitive_subject}</div>
      )}

      <div className="candidate-snippet">"{candidate.source_text?.slice(0, 60)}..."</div>

      <div className="candidate-card-actions" onClick={(e) => e.stopPropagation()}>
        {candidate.status !== 'CONFIRMED' && (
          <button className="btn-action-confirm" title="采纳为正典" onClick={() => onDecide(candidate.id, 'CONFIRM')}>
            ✓ 确认
          </button>
        )}
        {candidate.status !== 'REJECTED' && (
          <button className="btn-action-reject" title="拒绝此主张" onClick={() => onDecide(candidate.id, 'REJECT')}>
            ✗ 拒绝
          </button>
        )}
        {candidate.status !== 'DEFERRED' && (
          <button className="btn-action-defer" title="稍后处理" onClick={() => onDecide(candidate.id, 'DEFER')}>
            ⏸ 延后
          </button>
        )}
      </div>
    </div>
  )
}
