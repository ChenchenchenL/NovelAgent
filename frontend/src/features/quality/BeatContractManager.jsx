import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function BeatContractManager({ currentSceneId }) {
  const [beats, setBeats] = useState([])
  const [advDesc, setAdvDesc] = useState('')
  const [advType, setAdvType] = useState('NEW_ACTION')
  const [targetWords, setTargetWords] = useState(500)
  const [activeAdvanceBeatId, setActiveAdvanceBeatId] = useState(null)
  const [advanceInput, setAdvanceInput] = useState('')

  const loadBeats = async () => {
    if (!currentSceneId) return
    try {
      const res = await api.getSceneBeats(currentSceneId)
      setBeats(res || [])
    } catch (err) { console.error(err) }
  }

  useEffect(() => { loadBeats() }, [currentSceneId])

  const handleCreateBeat = async (e) => {
    e.preventDefault()
    if (!currentSceneId || !advDesc.trim()) return
    try {
      await api.createSceneBeat(currentSceneId, {
        required_advancements: [{ type: advType, description: advDesc.trim() }],
        stop_conditions: [{ type: 'WORD_COUNT', target: Number(targetWords) }],
        target_word_count: Number(targetWords),
      })
      setAdvDesc('')
      loadBeats()
    } catch (err) { console.error(err) }
  }

  const handleAdvanceSubmit = async (beatId) => {
    if (!advanceInput.trim()) return
    try {
      await api.advanceBeat(beatId, { advancement: { type: 'NEW_ACTION', description: advanceInput.trim() } })
      setActiveAdvanceBeatId(null)
      setAdvanceInput('')
      loadBeats()
    } catch (err) { console.error(err) }
  }

  const handleStop = async (beatId) => {
    try {
      await api.stopBeat(beatId, { reason: 'MANUAL_STOP' })
      loadBeats()
    } catch (err) { console.error(err) }
  }

  if (!currentSceneId) return <div className="empty-state">请先在左侧选择场景以管理节拍契约</div>

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreateBeat} className="continuity-form">
        <select value={advType} onChange={(e) => setAdvType(e.target.value)}>
          <option value="NEW_ACTION">新行动</option>
          <option value="NEW_INFO">新信息</option>
          <option value="NEW_DECISION">新决策</option>
          <option value="RELATIONSHIP_CHANGE">关系变化</option>
          <option value="CONFLICT_ESCALATION">冲突升级</option>
        </select>
        <input
          type="text" placeholder="推进声明 (如: 林舟夜探古寺)..."
          value={advDesc} onChange={(e) => setAdvDesc(e.target.value)} style={{ flex: 1 }}
        />
        <input
          type="number" placeholder="字数"
          value={targetWords} onChange={(e) => setTargetWords(e.target.value)} style={{ width: '80px' }}
        />
        <button type="submit" className="btn-primary">创建节拍</button>
      </form>

      <div className="continuity-list">
        {beats.length === 0 && <div className="empty-state">当前场景尚未创建节拍契约约束</div>}
        {beats.map((b) => (
          <div key={b.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>节拍 #{b.id}</strong> (目标: {b.target_word_count || 0} 字)</span>
              <span className={`badge ${b.status === 'COMPLETED' ? 'success' : (b.status === 'OVERRUN' ? 'warning' : 'gray')}`}>{b.status}</span>
            </div>
            <div style={{ marginTop: '6px', fontSize: '13px' }}>
              <div><strong>要求:</strong> {b.required_advancements.map((r, i) => <span key={i} className="badge gray">[{r.type}] {r.description}</span>)}</div>
              <div style={{ marginTop: '4px' }}><strong>已达成:</strong> {b.advancements_achieved.length === 0 ? '无' : b.advancements_achieved.map((a, i) => <span key={i} className="badge success">[{a.type}] {a.description}</span>)}</div>
            </div>
            {activeAdvanceBeatId === b.id ? (
              <div style={{ marginTop: '8px', display: 'flex', gap: '6px' }}>
                <input type="text" placeholder="输入推进描述..." value={advanceInput} onChange={(e) => setAdvanceInput(e.target.value)} style={{ flex: 1 }} />
                <button className="btn-small btn-primary" onClick={() => handleAdvanceSubmit(b.id)}>提交</button>
                <button className="btn-small" onClick={() => setActiveAdvanceBeatId(null)}>取消</button>
              </div>
            ) : (
              <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                <button className="btn-small" onClick={() => { setActiveAdvanceBeatId(b.id); setAdvanceInput('') }}>推进标记</button>
                <button className="btn-small" onClick={() => handleStop(b.id)}>停止契约</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
