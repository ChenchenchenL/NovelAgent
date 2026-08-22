import React, { useState, useEffect } from 'react'
import { api } from '../../../api/client'

export function ContextTab({ scene }) {
  const [report, setReport] = useState(null)
  const [intentionalCut, setIntentionalCut] = useState(false)
  const [loading, setLoading] = useState(false)

  const loadReport = async () => {
    if (!scene?.id) return
    setLoading(true)
    try {
      const res = await api.getSceneTransitionReport(scene.id)
      setReport(res)
      setIntentionalCut(Boolean(scene?.entry_contract?.intentional_cut))
    } catch {
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadReport() }, [scene?.id])

  const handleToggleIntentionalCut = async () => {
    if (!scene?.id) return
    const nextVal = !intentionalCut
    setIntentionalCut(nextVal)
    try {
      const existing = scene.entry_contract || {}
      await api.updateSceneContracts(scene.id, {
        entry_contract: { ...existing, intentional_cut: nextVal },
      })
      await loadReport()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="inspector-tab-content context-tab">
      <div className="scene-quick-props">
        <div className="prop-row">
          <span className="prop-label">叙事视点 (POV):</span>
          <span className="prop-val">{scene?.pov || '未设置'}</span>
        </div>
        <div className="prop-row">
          <span className="prop-label">发生地点:</span>
          <span className="prop-val">{scene?.location || '未设置'}</span>
        </div>
        <div className="prop-row">
          <span className="prop-label">叙事时间:</span>
          <span className="prop-val">{scene?.narrative_time || '跟随前文'}</span>
        </div>
      </div>

      <div className="transition-section" style={{ marginTop: '12px' }}>
        <div className="section-header-flex">
          <h4 className="section-title">7 维过渡连续性检查</h4>
          <label className="checkbox-toggle">
            <input type="checkbox" checked={intentionalCut} onChange={handleToggleIntentionalCut} />
            <span>文学留白 / 跳切</span>
          </label>
        </div>

        {loading ? (
          <div className="empty-hint">校验时空与人物连续性中...</div>
        ) : report ? (
          <div className="transition-results">
            <div className={`transition-summary-badge status-${(report.status || '').toLowerCase()}`}>
              评级: {report.status}
            </div>
            <div className="dimension-checks-list">
              {(report.checks || []).map((c, i) => (
                <div key={i} className="dim-check-item">
                  <div className="dim-header">
                    <strong>{c.dimension}</strong>
                    <span className={`badge-sm status-${(c.status || '').toLowerCase()}`}>{c.status}</span>
                  </div>
                  <p className="dim-msg">{c.message}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty-hint">暂无相邻场景过渡分析</div>
        )}
      </div>
    </div>
  )
}
