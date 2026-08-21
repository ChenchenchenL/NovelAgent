import React, { useState } from 'react'
import { useExtraction } from '../hooks/useExtraction'
import { CandidateCard } from './CandidateCard'
import { EvidenceViewer } from './EvidenceViewer'
import { AliasManager } from './AliasManager'
import { ConflictResolutionDialog } from './ConflictResolutionDialog'

export function ArbitrationWorkbench({ sceneId }) {
  const { candidates, canonClaims, conflicts, loading, error, runExtraction, decide, batchDecide, reload } = useExtraction(sceneId)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [activeConflict, setActiveConflict] = useState(null)
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [showAliasModal, setShowAliasModal] = useState(false)

  const filteredCandidates = candidates.filter((c) => {
    if (statusFilter !== 'ALL' && c.status !== statusFilter) return false
    return true
  })

  const handleAutoConfirmAllLowRisk = async () => {
    const lowRisk = candidates.filter((c) => c.status === 'AUTO_CONFIRMED' || (c.modality === 'ACTUAL' && c.confidence >= 0.85 && c.status === 'REVIEW_REQUIRED'))
    if (!lowRisk.length) return
    await batchDecide(lowRisk.map((c) => ({ id: c.id, decision: 'CONFIRM' })))
  }

  const handleResolveConflict = async (conflictId, option) => {
    setActiveConflict(null)
    await reload()
  }

  return (
    <div className="arbitration-workbench">
      <div className="arbitration-toolbar">
        <div className="toolbar-left">
          <button className="btn-primary" disabled={loading} onClick={() => runExtraction(true)}>
            {loading ? '抽取中...' : '🔍 重新逆向抽取'}
          </button>
          <button className="btn-secondary" onClick={handleAutoConfirmAllLowRisk}>
            ✓ 一键采纳低风险主张
          </button>
          <button className="btn-secondary" onClick={() => setShowAliasModal(true)}>
            ⚡ 别名消歧库
          </button>
        </div>

        <div className="toolbar-right">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="ALL">全部状态 ({candidates.length})</option>
            <option value="REVIEW_REQUIRED">待审核 ({candidates.filter((c) => c.status === 'REVIEW_REQUIRED').length})</option>
            <option value="AUTO_CONFIRMED">自动确认候选 ({candidates.filter((c) => c.status === 'AUTO_CONFIRMED').length})</option>
            <option value="CONFIRMED">已确认正典 ({canonClaims.length})</option>
            <option value="DEFERRED">已延后</option>
          </select>
        </div>
      </div>

      {conflicts.length > 0 && (
        <div className="conflict-banner">
          ⚠️ 发现 {conflicts.length} 处硬逻辑冲突（点击解决）：
          {conflicts.map((conf) => (
            <button key={conf.id} className="conflict-tag-btn" onClick={() => setActiveConflict(conf)}>
              {conf.message}
            </button>
          ))}
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="arbitration-panes">
        <div className="candidates-list-pane">
          {filteredCandidates.length === 0 ? (
            <div className="empty">暂无匹配的候选主张</div>
          ) : (
            filteredCandidates.map((c) => (
              <CandidateCard
                key={c.id} candidate={c} isSelected={selectedCandidate?.id === c.id}
                onSelect={setSelectedCandidate} onDecide={(id, dec) => decide(id, dec)}
              />
            ))
          )}
        </div>

        <div className="evidence-detail-pane">
          <EvidenceViewer
            candidate={selectedCandidate}
            onSaveDecision={(id, dec, corr, notes) => decide(id, dec, corr, notes)}
            onCancel={() => setSelectedCandidate(null)}
          />
        </div>
      </div>

      {showAliasModal && <AliasManager onClose={() => setShowAliasModal(false)} />}
      {activeConflict && (
        <ConflictResolutionDialog
          conflict={activeConflict}
          onClose={() => setActiveConflict(null)}
          onResolve={handleResolveConflict}
        />
      )}
    </div>
  )
}
