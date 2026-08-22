import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ForeshadowingManager({ currentSceneId }) {
  const [foreshadowings, setForeshadowings] = useState([])
  const [name, setName] = useState('')
  const [priority, setPriority] = useState('SUBPLOT')
  const [startChap, setStartChap] = useState('')
  const [endChap, setEndChap] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try { setForeshadowings((await api.getForeshadowings()) || []) } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [currentSceneId])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createForeshadowing({
        name: name.trim(), setup_scene_id: currentSceneId || 1, priority,
        target_chapter_start: startChap ? Number(startChap) : null,
        target_chapter_end: endChap ? Number(endChap) : null,
        trigger_condition_type: 'EVENT_OCCURS', confirmed: true,
      })
      setName(''); setStartChap(''); setEndChap(''); await loadData()
    } finally { setLoading(false) }
  }

  const handlePayoff = async (id) => {
    const desc = prompt('请输入伏笔揭开/回收剧情说明:')
    if (!desc) return
    await api.payoffForeshadowing(id, { payoff_scene_id: currentSceneId || 1, description: desc.trim() })
    await loadData()
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreate} className="continuity-form-card">
        <span style={{ fontSize: '13px', fontWeight: 650, color: '#09090b' }}>埋设新伏笔或悬念</span>
        <div className="continuity-form-row">
          <input placeholder="伏笔名称 * (例如: 废弃芯片中的灭门真相)" value={name} onChange={e => setName(e.target.value)} required />
          <select value={priority} onChange={e => setPriority(e.target.value)}>
            <option value="MAIN">主线核心伏笔</option>
            <option value="SUBPLOT">支线秘密伏笔</option>
            <option value="BACKGROUND">世界观背景暗示</option>
          </select>
          <input type="number" placeholder="预计揭晓章 (例如: 10)" value={endChap} onChange={e => setEndChap(e.target.value)} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={loading} className="btn-blue">埋设伏笔</button>
        </div>
      </form>

      <div className="continuity-cards-grid">
        {foreshadowings.map(f => (
          <div key={f.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong style={{ fontSize: '13.5px', color: '#09090b' }}>{f.name}</strong>
              {f.status === 'SETUP' ? (
                <button onClick={() => handlePayoff(f.id)} className="mini-btn btn-blue">回收揭晓</button>
              ) : (
                <span className="status-ready-badge">已回收</span>
              )}
            </div>
            <p className="card-desc">预计揭晓区间：第 {f.target_chapter_start || 1} ~ {f.target_chapter_end || '待定'} 章</p>
          </div>
        ))}
      </div>
      {foreshadowings.length === 0 && <div className="empty-state">暂无埋设伏笔记录</div>}
    </div>
  )
}
