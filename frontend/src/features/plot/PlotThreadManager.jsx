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
  const [eventType, setEventType] = useState('DEVELOPMENT')
  const [eventDesc, setEventDesc] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const data = await api.getPlotThreads()
      setThreads(data)
      if (selectedThread) {
        const evts = await api.getPlotThreadEvents(selectedThread.id)
        setEvents(evts)
      }
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [selectedThread?.id])

  const handleCreateThread = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createPlotThread({ name, thread_type: threadType, priority: Number(priority), description: desc, start_scene_id: currentSceneId })
      setName(''); setDesc(''); await loadData()
    } finally { setLoading(false) }
  }

  const handleAddEvent = async (e) => {
    e.preventDefault()
    if (!selectedThread || !eventDesc.trim() || !currentSceneId) return alert('需选中剧情线与当前场景')
    setLoading(true)
    try {
      await api.createPlotEvent(selectedThread.id, { plot_thread_id: selectedThread.id, event_type: eventType, scene_id: currentSceneId, description: eventDesc, confirmed: true })
      setEventDesc(''); await loadData()
    } finally { setLoading(false) }
  }

  const handleStatusChange = async (id, status) => {
    await api.updatePlotThread(id, { status })
    await loadData()
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreateThread} className="continuity-form">
        <input placeholder="剧情线名称 *" value={name} onChange={e => setName(e.target.value)} required />
        <select value={threadType} onChange={e => setThreadType(e.target.value)}>
          <option value="MAIN">主线 (MAIN)</option>
          <option value="SUBPLOT">支线 (SUBPLOT)</option>
          <option value="CHARACTER_ARC">人物弧 (CHARACTER_ARC)</option>
          <option value="MYSTERY">悬念 (MYSTERY)</option>
        </select>
        <select value={priority} onChange={e => setPriority(e.target.value)}>
          <option value="1">优先级 1 (核心)</option>
          <option value="2">优先级 2 (重要)</option>
          <option value="3">优先级 3 (背景)</option>
        </select>
        <input placeholder="描述说明" value={desc} onChange={e => setDesc(e.target.value)} />
        <button type="submit" disabled={loading} className="btn-primary">新增剧情线</button>
      </form>
      <div className="plot-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div className="continuity-list">
          {threads.map(t => (
            <div key={t.id} className={`continuity-card ${selectedThread?.id === t.id ? 'active' : ''}`} onClick={() => setSelectedThread(t)} style={{ cursor: 'pointer' }}>
              <div className="continuity-card-header">
                <strong>{t.name}</strong>
                <select value={t.status} onClick={e => e.stopPropagation()} onChange={e => handleStatusChange(t.id, e.target.value)} className="status-select">
                  <option value="ACTIVE">进行中</option><option value="RESOLVED">已解决</option><option value="ABANDONED">已废弃</option><option value="SUSPENDED">暂停</option>
                </select>
              </div>
              <p className="card-desc">{t.description || '无描述'}</p>
              <div className="tag-row"><span className="badge">{t.thread_type}</span><span className="badge gray">优先级 {t.priority}</span></div>
            </div>
          ))}
        </div>
        <div>
          {selectedThread ? (
            <div className="continuity-card">
              <h4>事件时间线: {selectedThread.name}</h4>
              <form onSubmit={handleAddEvent} className="continuity-form" style={{ marginTop: '8px' }}>
                <select value={eventType} onChange={e => setEventType(e.target.value)}>
                  <option value="DEVELOPMENT">推进 (DEVELOPMENT)</option><option value="TWIST">转折 (TWIST)</option><option value="DELAY">延迟 (DELAY)</option><option value="RESOLUTION">解决 (RESOLUTION)</option><option value="ABANDONED">废弃 (ABANDONED)</option>
                </select>
                <input placeholder="事件描述 *" value={eventDesc} onChange={e => setEventDesc(e.target.value)} required />
                <button type="submit" disabled={loading || !currentSceneId} className="btn-primary">记录事件</button>
              </form>
              <div className="timeline-list" style={{ marginTop: '8px', maxHeight: '240px', overflowY: 'auto' }}>
                {events.map(ev => (
                  <div key={ev.id} className="timeline-item" style={{ borderLeft: '2px solid #3b82f6', paddingLeft: '8px', marginBottom: '6px' }}>
                    <span className="badge">{ev.event_type}</span> <small>场景 #{ev.scene_id}</small>
                    <p style={{ margin: '2px 0', fontSize: '13px' }}>{ev.description}</p>
                  </div>
                ))}
                {events.length === 0 && <div className="empty-state">暂无事件记录</div>}
              </div>
            </div>
          ) : <div className="empty-state">点击左侧剧情线查看/记录事件</div>}
        </div>
      </div>
    </div>
  )
}
