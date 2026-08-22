import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function PlotThreadManager({ currentSceneId }) {
  const [threads, setThreads] = useState([])
  const [name, setName] = useState('')
  const [threadType, setThreadType] = useState('MAIN')
  const [priority, setPriority] = useState(1)
  const [desc, setDesc] = useState('')
  const [selectedThread, setSelectedThread] = useState(null)
  const [events, setEvents] = useState([])
  const [eventDesc, setEventDesc] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const data = await api.getPlotThreads()
      setThreads(data || [])
      if (selectedThread) setEvents((await api.getPlotThreadEvents(selectedThread.id)) || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [selectedThread?.id])

  const handleCreateThread = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createPlotThread({ name: name.trim(), thread_type: threadType, priority: Number(priority), description: desc.trim(), start_scene_id: currentSceneId })
      setName(''); setDesc(''); await loadData()
    } finally { setLoading(false) }
  }

  const handleAddEvent = async (e) => {
    e.preventDefault()
    if (!selectedThread || !eventDesc.trim() || !currentSceneId) return alert('需先选中剧情线与当前场景')
    setLoading(true)
    try {
      await api.createPlotEvent(selectedThread.id, { plot_thread_id: selectedThread.id, event_type: 'DEVELOPMENT', scene_id: currentSceneId, description: eventDesc.trim(), confirmed: true })
      setEventDesc(''); await loadData()
    } finally { setLoading(false) }
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreateThread} className="continuity-form-card">
        <span style={{ fontSize: '13px', fontWeight: 650, color: '#09090b' }}>创建新剧情线</span>
        <div className="continuity-form-row">
          <input placeholder="剧情线名称 * (如: 身世揭秘与复仇)" value={name} onChange={e => setName(e.target.value)} required />
          <select value={threadType} onChange={e => setThreadType(e.target.value)}>
            <option value="MAIN">主线 (MAIN)</option>
            <option value="SUBPLOT">支线 (SUBPLOT)</option>
            <option value="CHARACTER_ARC">人物成长弧 (ARC)</option>
          </select>
          <select value={priority} onChange={e => setPriority(e.target.value)}>
            <option value="1">优先级 1 (核心主线)</option>
            <option value="2">优先级 2 (重要支线)</option>
            <option value="3">优先级 3 (背景暗线)</option>
          </select>
        </div>
        <input placeholder="剧情线起因、发展与预期结局简述" value={desc} onChange={e => setDesc(e.target.value)} />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={loading} className="btn-blue">新增剧情线</button>
        </div>
      </form>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {threads.map(t => (
            <div key={t.id} className={`continuity-card ${selectedThread?.id === t.id ? 'active' : ''}`} onClick={() => setSelectedThread(t)} style={{ cursor: 'pointer' }}>
              <div className="continuity-card-header">
                <strong style={{ fontSize: '13.5px', color: '#09090b' }}>{t.name}</strong>
                <span className="badge blue">{t.thread_type === 'MAIN' ? '核心主线' : '支线'}</span>
              </div>
              <p className="card-desc">{t.description || '无具体描述'}</p>
            </div>
          ))}
          {threads.length === 0 && <div className="empty-state">暂无剧情线</div>}
        </div>

        <div>
          {selectedThread ? (
            <div className="continuity-card">
              <span style={{ fontSize: '13px', fontWeight: 650 }}>{selectedThread.name} · 推进时间线</span>
              <form onSubmit={handleAddEvent} style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                <input placeholder="记录本场关键剧情进展..." value={eventDesc} onChange={e => setEventDesc(e.target.value)} style={{ flex: 1 }} required />
                <button type="submit" disabled={loading || !currentSceneId} className="btn-small btn-blue">记录</button>
              </form>
              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {events.map(ev => (
                  <div key={ev.id} style={{ padding: '6px 10px', background: '#f8fafc', borderLeft: '2px solid #2563eb', fontSize: '12.5px' }}>
                    <span>{ev.description}</span>
                  </div>
                ))}
                {events.length === 0 && <div className="empty-state">暂无推进事件记录</div>}
              </div>
            </div>
          ) : <div className="empty-state">点击左侧剧情线可查看或记录推进事件</div>}
        </div>
      </div>
    </div>
  )
}
