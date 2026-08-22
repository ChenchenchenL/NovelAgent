import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function GlobalAuditPanel() {
  const [reports, setReports] = useState([])
  const [activeReport, setActiveReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadReports = async () => {
    try {
      const res = await api.getGlobalAnalysisReports()
      setReports(res || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadReports() }, [])

  const handleRunAudit = async (auditType) => {
    setLoading(true)
    try {
      let res
      if (auditType === 'CHARACTER_ARC') res = await api.runCharacterArcsAnalysis()
      else if (auditType === 'RELATIONSHIP_NETWORK') res = await api.runRelationshipNetworkAnalysis()
      else if (auditType === 'FORESHADOW_AUDIT') res = await api.runForeshadowAudit()
      else if (auditType === 'PLOT_RUPTURE') res = await api.runPlotRuptureAudit()
      setActiveReport(res)
      loadReports()
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button className="btn-small btn-primary" onClick={() => handleRunAudit('CHARACTER_ARC')} disabled={loading}>
          🎭 人物弧回顾
        </button>
        <button className="btn-small btn-primary" onClick={() => handleRunAudit('RELATIONSHIP_NETWORK')} disabled={loading}>
          🕸️ 关系网全景
        </button>
        <button className="btn-small btn-primary" onClick={() => handleRunAudit('FORESHADOW_AUDIT')} disabled={loading}>
          🎯 伏笔兑现审计
        </button>
        <button className="btn-small btn-primary" onClick={() => handleRunAudit('PLOT_RUPTURE')} disabled={loading}>
          🚨 剧情断裂检测
        </button>
      </div>

      {activeReport && (
        <div className="continuity-card" style={{ marginBottom: '16px', background: '#252028' }}>
          <div className="continuity-card-header">
            <strong>全书审计报告: [{activeReport.report_type}]</strong>
            <span className="badge success">耗时: {activeReport.duration_ms}ms</span>
          </div>
          <p style={{ marginTop: '8px', fontSize: '14px' }}>{activeReport.summary}</p>
          <pre style={{ marginTop: '8px', fontSize: '12px', background: '#18151c', padding: '8px', borderRadius: '4px', maxHeight: '200px', overflowY: 'auto' }}>
            {JSON.stringify(activeReport.content, null, 2)}
          </pre>
        </div>
      )}

      <h4>历史全局审计报告 ({reports.length} 份)</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {reports.map((r) => (
          <div key={r.id} className="continuity-card" style={{ cursor: 'pointer' }} onClick={() => setActiveReport(r)}>
            <div className="continuity-card-header">
              <span><strong>[{r.report_type}]</strong> {r.summary}</span>
              <span className="badge gray">ID #{r.id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
