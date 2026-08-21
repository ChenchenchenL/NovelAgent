import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function FeedbackStatsPanel() {
  const [stats, setStats] = useState(null)
  const [feedbacks, setFeedbacks] = useState([])

  const loadData = async () => {
    try {
      const [s, f] = await Promise.all([api.getAuthorFeedbackStats(), api.getAuthorFeedback()])
      setStats(s)
      setFeedbacks(f || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [])

  return (
    <div className="continuity-subpanel">
      {stats && (
        <div className="continuity-card" style={{ marginBottom: '16px' }}>
          <div className="continuity-card-header">
            <strong>作者反馈与去噪审计 (总反馈: {stats.total_feedback} 条)</strong>
            <span className="badge success">误报率: {Math.round(stats.false_positive_rate * 100)}%</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', display: 'flex', gap: '16px' }}>
            <span>采纳修改: <strong>{stats.accept_count}</strong></span>
            <span>拒绝修改: <strong>{stats.reject_count}</strong></span>
            <span>忽略/文学放行: <strong>{stats.ignore_count}</strong></span>
          </div>
        </div>
      )}

      <h4>反馈记录历史</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {feedbacks.length === 0 && <div className="empty-state">暂无作者反馈记录</div>}
        {feedbacks.map((fb) => (
          <div key={fb.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>[{fb.issue_type}]</strong> 决定: <span className="badge gray">{fb.decision}</span></span>
              <span className="badge success">范围: {fb.scope}</span>
            </div>
            {fb.reason && <p style={{ marginTop: '4px', fontSize: '12px', color: '#aaa' }}>理由: {fb.reason}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
