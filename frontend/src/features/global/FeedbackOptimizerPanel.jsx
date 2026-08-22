import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function FeedbackOptimizerPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadSuggestions = async () => {
    try {
      const res = await api.getFeedbackOptimizationSuggestions()
      setData(res)
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadSuggestions() }, [])

  const handleApply = async (issueType) => {
    setLoading(true)
    try {
      await api.applyFeedbackOptimization({ issue_type: issueType, action: 'SUPPRESS' })
      loadSuggestions()
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ marginBottom: '16px' }}>
        <h4>反馈驱动的去噪与规则优化建议</h4>
        <p style={{ fontSize: '13px', color: '#888', marginTop: '4px' }}>
          根据作者对误报质检建议的忽略/拒绝统计，自动提炼去噪规则与放行建议。
        </p>
      </div>

      {data && (
        <div>
          <div className="continuity-card" style={{ marginBottom: '16px' }}>
            <div className="continuity-card-header">
              <strong>反馈总样本: {data.feedback_summary?.total_feedback || 0} 条</strong>
              <span className="badge success">全局误报率: {Math.round((data.feedback_summary?.false_positive_rate || 0) * 100)}%</span>
            </div>
          </div>

          <h4>针对性优化建议 ({data.suggestions?.length || 0} 项)</h4>
          <div className="continuity-list" style={{ marginTop: '8px' }}>
            {(!data.suggestions || data.suggestions.length === 0) && (
              <div className="empty-state">当前未发现高误报率规则，质控系统运行健康</div>
            )}
            {data.suggestions?.map((s, i) => (
              <div key={i} className="continuity-card">
                <div className="continuity-card-header">
                  <span><span className="badge warning">[{s.issue_type}]</span> <strong>误报率: {Math.round(s.false_positive_rate * 100)}%</strong></span>
                  <button className="btn-small btn-primary" onClick={() => handleApply(s.issue_type)} disabled={loading}>
                    一键全局放行
                  </button>
                </div>
                <p style={{ marginTop: '6px', fontSize: '13px' }}>{s.reason}</p>
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#888' }}>💡 优化措施: {s.recommended_fix}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
