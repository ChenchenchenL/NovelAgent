import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function FeedbackOptimizerPanel() {
  const [stats, setStats] = useState(null)
  const [proposals, setProposals] = useState([])
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [s, p] = await Promise.all([
        api.getAuthorFeedbackStats(),
        api.getOptimizationProposals(),
      ])
      setStats(s)
      setProposals(p || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  const handleRunOptimize = async () => {
    setOptimizing(true)
    try {
      await api.runFeedbackOptimization()
      await loadData()
    } catch (e) { console.error(e) }
    finally { setOptimizing(false) }
  }

  const handleApply = async (propId) => {
    try {
      await api.applyOptimizationProposal(propId)
      await loadData()
    } catch (e) { console.error(e) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4>作者反馈聚合与规则调优建议</h4>
        <button className="btn-primary" onClick={handleRunOptimize} disabled={optimizing}>
          {optimizing ? '计算调优中...' : '运行反馈规则优化'}
        </button>
      </div>

      {stats && (
        <div className="continuity-card" style={{ marginBottom: '16px' }}>
          <div className="continuity-card-header">
            <strong>反馈统计 (总反馈: {stats.total_feedback_count} 次)</strong>
            <span className="badge success">去噪建议: {stats.proposed_rules_count} 条</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px' }}>
            <span>采纳率: <strong>{Math.round(stats.acceptance_rate * 100)}%</strong></span> |{' '}
            <span>忽略/放行: <strong>{stats.ignore_count} 次</strong></span>
          </div>
        </div>
      )}

      <h4>规则与参数调优提案 ({proposals.length} 项)</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {proposals.length === 0 && <div className="empty-state">当前暂无待优化的规则提案</div>}
        {proposals.map((p) => (
          <div key={p.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>[{p.proposal_type}]</strong> {p.description}</span>
              {p.status === 'PROPOSED' ? (
                <button className="btn-small btn-primary" onClick={() => handleApply(p.id)}>应用调整</button>
              ) : (
                <span className="badge success">已应用</span>
              )}
            </div>
            <p style={{ marginTop: '6px', fontSize: '12px', color: '#888' }}>
              依据: 基于 {p.evidence_feedback_count} 次相关历史反馈
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
