import React, { useState, useEffect } from 'react'
import { api } from '../../../api/client'

export function SceneBeatsTab({ scene }) {
  const [beats, setBeats] = useState([])
  const [advDesc, setAdvDesc] = useState('')
  const [advType, setAdvType] = useState('NEW_ACTION')
  const [targetWords, setTargetWords] = useState(500)

  const loadBeats = async () => {
    if (!scene?.id) return
    try {
      const res = await api.getSceneBeats(scene.id)
      setBeats(res || [])
    } catch {
      setBeats([])
    }
  }

  useEffect(() => { loadBeats() }, [scene?.id])

  const handleCreateBeat = async (e) => {
    e.preventDefault()
    if (!scene?.id || !advDesc.trim()) return
    try {
      await api.createSceneBeat(scene.id, {
        required_advancements: [{ type: advType, description: advDesc.trim() }],
        stop_conditions: [{ type: 'WORD_COUNT', target: Number(targetWords) }],
        target_word_count: Number(targetWords),
      })
      setAdvDesc('')
      loadBeats()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="inspector-tab-content beats-tab">
      <div className="tab-section">
        <h4 className="section-title">节拍推进契约 ({beats.length})</h4>
        <form onSubmit={handleCreateBeat} className="beat-quick-form">
          <div className="form-row-compact">
            <select value={advType} onChange={(e) => setAdvType(e.target.value)}>
              <option value="NEW_ACTION">新行动</option>
              <option value="NEW_INFO">新信息</option>
              <option value="NEW_DECISION">新决策</option>
              <option value="RELATIONSHIP_CHANGE">关系变化</option>
              <option value="CONFLICT_ESCALATION">冲突升级</option>
            </select>
            <input
              type="number" style={{ width: '70px' }}
              value={targetWords} onChange={(e) => setTargetWords(e.target.value)}
              placeholder="字数"
            />
          </div>
          <div className="form-row-compact" style={{ marginTop: '4px' }}>
            <input
              type="text" placeholder="推进目标 (如: 主角发现密信)..."
              value={advDesc} onChange={(e) => setAdvDesc(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn-sm primary">添加节拍</button>
          </div>
        </form>

        <div className="beats-list">
          {beats.length === 0 ? (
            <div className="empty-hint">当前场景尚未配置节拍推进目标</div>
          ) : (
            beats.map((b) => (
              <div key={b.id} className="beat-card">
                <div className="beat-card-top">
                  <span><strong>节拍 #{b.id}</strong> (目标 {b.target_word_count} 字)</span>
                  <span className={`badge-sm status-${(b.status || '').toLowerCase()}`}>{b.status}</span>
                </div>
                <div className="beat-requirements">
                  {b.required_advancements.map((r, i) => (
                    <span key={i} className="req-tag">[{r.type}] {r.description}</span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="tab-section" style={{ marginTop: '14px' }}>
        <h4 className="section-title">场景进入与退出契约</h4>
        <div className="contracts-compact">
          <div className="contract-box">
            <div className="contract-label">SceneEntryContract (进入约束)</div>
            <pre>{JSON.stringify(scene?.entry_contract || { note: '继承上场' }, null, 2)}</pre>
          </div>
          <div className="contract-box" style={{ marginTop: '6px' }}>
            <div className="contract-label">SceneExitState (退出状态)</div>
            <pre>{JSON.stringify(scene?.exit_state || { note: '写作完成后生成' }, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  )
}
