import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

const DIMENSION_NAMES = {
  TIME: '时间',
  SPACE: '空间',
  CHARACTER: '人物',
  ACTION: '行动',
  EMOTION: '情绪',
  INFORMATION: '信息',
  POV: 'POV视角',
}

export function TransitionInspector({ currentSceneId }) {
  const [report, setReport] = useState(null)
  const [sceneData, setSceneData] = useState(null)
  const [intentionalCut, setIntentionalCut] = useState(false)
  const [loading, setLoading] = useState(false)

  const loadReport = async () => {
    if (!currentSceneId) return
    setLoading(true)
    try {
      const [res, sc] = await Promise.all([
        api.getSceneTransitionReport(currentSceneId),
        api.getScene(currentSceneId),
      ])
      setReport(res)
      setSceneData(sc)
      setIntentionalCut(Boolean(sc?.entry_contract?.intentional_cut))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadReport() }, [currentSceneId])

  const handleToggleIntentionalCut = async () => {
    if (!currentSceneId) return
    const nextVal = !intentionalCut
    setIntentionalCut(nextVal)
    const existingEntry = sceneData?.entry_contract || {}
    await api.updateSceneContracts(currentSceneId, {
      entry_contract: { ...existingEntry, intentional_cut: nextVal },
    })
    await loadReport()
  }

  return (
    <div className="continuity-subpanel">
      {!currentSceneId ? (
        <div className="empty-state">请先在左侧大纲选中场景查看场景过渡分析</div>
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h4>场景 #{currentSceneId} 过渡连续性分析</h4>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={intentionalCut} onChange={handleToggleIntentionalCut} />
              <span>标记为有意跳切 (INTENTIONAL_CUT / 文学留白)</span>
            </label>
          </div>
          {report && (
            <div>
              <div className="continuity-card" style={{ marginBottom: '12px' }}>
                <strong>综合状态: </strong>
                <span className={`badge ${report.status === 'OK' ? 'success' : (report.status === 'CONFLICT' ? 'danger' : (report.status === 'INTENTIONAL_CUT' ? 'gray' : 'warning'))}`}>
                  {report.status}
                </span>
                <p style={{ marginTop: '6px', fontSize: '13px' }}>{report.message}</p>
              </div>
              <div className="continuity-list">
                {(report.checks || []).map((c, idx) => (
                  <div key={idx} className="continuity-card">
                    <div className="continuity-card-header">
                      <span><strong>{c.dimension}</strong> ({DIMENSION_NAMES[c.dimension] || c.dimension})</span>
                      <span className={`badge ${c.status === 'OK' ? 'success' : (c.status === 'CONFLICT' ? 'danger' : 'warning')}`}>{c.status}</span>
                    </div>
                    <p className="card-desc">{c.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
