import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ForeshadowingManager({ currentSceneId }) {
  const [foreshadowings, setForeshadowings] = useState([])
  const [scheduled, setScheduled] = useState([])
  const [name, setName] = useState('')
  const [priority, setPriority] = useState('SUBPLOT')
  const [startChap, setStartChap] = useState('')
  const [endChap, setEndChap] = useState('')
  const [trigType, setTrigType] = useState('CHARACTER_ARRIVES')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const list = await api.getForeshadowings()
      setForeshadowings(list)
      if (currentSceneId) {
        const sched = await api.getScheduledForeshadowings(currentSceneId)
        setScheduled(sched)
      }
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [currentSceneId])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim() || !currentSceneId) return alert('需输入名称并在左侧选定埋设场景')
    setLoading(true)
    try {
      await api.createForeshadowing({
        name,
        setup_scene_id: currentSceneId,
        priority,
        target_chapter_start: startChap ? Number(startChap) : null,
        target_chapter_end: endChap ? Number(endChap) : null,
        trigger_condition_type: trigType,
        confirmed: true,
      })
      setName(''); setStartChap(''); setEndChap(''); await loadData()
    } finally { setLoading(false) }
  }

  const handlePayoff = async (id) => {
    if (!currentSceneId) return alert('请在左侧选择回收伏笔的场景')
    const desc = prompt('请输入伏笔回收剧情说明:')
    if (!desc) return
    await api.payoffForeshadowing(id, { payoff_scene_id: currentSceneId, description: desc })
    await loadData()
  }

  return (
    <div className="continuity-subpanel">
      {scheduled.length > 0 && (
        <div className="warning-banner" style={{ marginBottom: '12px' }}>
          <strong>当前场景伏笔调度建议 ({scheduled.length} 条):</strong>
          <div className="tag-row" style={{ marginTop: '4px' }}>
            {scheduled.map(s => (
              <span key={s.foreshadowing_id} className={`badge ${s.is_triggered ? 'success' : (s.is_overdue ? 'danger' : 'gray')}`}>
                {s.name} {s.is_triggered ? '条件满足' : (s.is_overdue ? '超期未收' : '窗口内')}
              </span>
            ))}
          </div>
        </div>
      )}
      <form onSubmit={handleCreate} className="continuity-form">
        <input placeholder="伏笔名称 *" value={name} onChange={e => setName(e.target.value)} required />
        <select value={priority} onChange={e => setPriority(e.target.value)}>
          <option value="MAIN">主线伏笔 (MAIN)</option>
          <option value="SUBPLOT">支线伏笔 (SUBPLOT)</option>
          <option value="BACKGROUND">背景伏笔 (BACKGROUND)</option>
        </select>
        <input type="number" placeholder="目标开始章" value={startChap} onChange={e => setStartChap(e.target.value)} style={{ width: '100px' }} />
        <input type="number" placeholder="目标结束章" value={endChap} onChange={e => setEndChap(e.target.value)} style={{ width: '100px' }} />
        <select value={trigType} onChange={e => setTrigType(e.target.value)}>
          <option value="CHARACTER_ARRIVES">人物到达 (CHARACTER_ARRIVES)</option>
          <option value="CHARACTER_OBTAINS">获得物品 (CHARACTER_OBTAINS)</option>
          <option value="CHARACTER_HEARS">听到关键词 (CHARACTER_HEARS)</option>
          <option value="EVENT_OCCURS">事件发生 (EVENT_OCCURS)</option>
        </select>
        <button type="submit" disabled={loading || !currentSceneId} className="btn-primary">埋设伏笔</button>
      </form>
      <div className="continuity-list">
        {foreshadowings.map(f => (
          <div key={f.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>{f.name}</strong> <span className="badge">{f.priority}</span></span>
              {f.status === 'SETUP' && <button onClick={() => handlePayoff(f.id)} className="btn-primary small">回收伏笔</button>}
              {f.status === 'PAYOFF' && <span className="badge success">已回收 (场景 #{f.payoff_scene_id})</span>}
            </div>
            <p className="card-desc">{f.description || `目标章节: 第 ${f.target_chapter_start || 1} ~ ${f.target_chapter_end || '未定'} 章`}</p>
            <div className="tag-row"><span className="badge gray">触发: {f.trigger_condition_type}</span><span className="badge gray">埋设场景 #{f.setup_scene_id}</span></div>
          </div>
        ))}
        {foreshadowings.length === 0 && <div className="empty-state">暂无伏笔记录</div>}
      </div>
    </div>
  )
}
