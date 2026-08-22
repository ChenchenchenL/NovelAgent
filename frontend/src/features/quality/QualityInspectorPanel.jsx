import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function QualityInspectorPanel({ currentSceneId }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadReport = async () => {
    if (!currentSceneId) return
    try {
      const res = await api.getSceneQualityReport(currentSceneId)
      setReport(res)
    } catch { setReport(null) }
  }

  useEffect(() => { loadReport() }, [currentSceneId])

  const handleRunCheck = async () => {
    if (!currentSceneId) return
    setLoading(true)
    try {
      const res = await api.checkSceneQuality(currentSceneId)
      setReport(res)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleFeedback = async (issueType, decision, scope = 'THIS_SCENE') => {
    try {
      await api.createAuthorFeedback({
        issue_type: issueType,
        decision,
        scope,
        scene_id: currentSceneId,
      })
      handleRunCheck()
    } catch (e) { console.error(e) }
  }

  if (!currentSceneId) return <div className="empty-state">请先在左侧选择场景以审查文本质量</div>

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4>场景文本质量与套话审查</h4>
        <button className="btn-primary" onClick={handleRunCheck} disabled={loading}>
          {loading ? '检查中...' : '执行质量检查'}
        </button>
      </div>

      {report ? (
        <div>
          <div className="continuity-card" style={{ marginBottom: '12px' }}>
            <div className="continuity-card-header">
              <span><strong>检测问题数: {report.summary.total}</strong> (硬冲突: {report.summary.blocking}, 警告: {report.summary.warning}, 建议: {report.summary.advisory})</span>
              <span className={`badge ${report.summary.has_blocking ? 'danger' : (report.summary.warning > 0 ? 'warning' : 'success')}`}>
                {report.summary.has_blocking ? '存在硬阻断' : (report.summary.warning > 0 ? '需关注' : '质量良好')}
              </span>
            </div>
          </div>

          <div className="continuity-list">
            {report.issues.length === 0 && <div className="empty-state">未发现语义重复、套话或水字数问题</div>}
            {report.issues.map((iss, idx) => (
              <div key={idx} className="continuity-card">
                <div className="continuity-card-header">
                  <span>
                    <span className={`badge ${iss.severity === 'BLOCKING' ? 'danger' : (iss.severity === 'WARNING' ? 'warning' : 'gray')}`}>
                      {iss.severity}
                    </span>{' '}
                    <strong>[{iss.issue_type}]</strong>
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button className="btn-small" onClick={() => handleFeedback(iss.issue_type, 'ACCEPT')}>采纳建议</button>
                    <button className="btn-small" onClick={() => handleFeedback(iss.issue_type, 'IGNORE', 'THIS_SCENE')}>本场放行</button>
                    <button className="btn-small" onClick={() => handleFeedback(iss.issue_type, 'IGNORE', 'ALWAYS')}>全局放行</button>
                  </div>
                </div>
                <p style={{ marginTop: '6px', fontSize: '13px' }}>{iss.description}</p>
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#888' }}>建议: {iss.suggestion}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">尚未对当前场景执行质量检查，请点击右上角按钮开始</div>
      )}
    </div>
  )
}
