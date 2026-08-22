import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function CommunityManager() {
  const [communities, setCommunities] = useState([])
  const [name, setName] = useState('')
  const [type, setType] = useState('CUSTOM')
  const [tag, setTag] = useState('')
  const [selectedComm, setSelectedComm] = useState(null)
  const [summaries, setSummaries] = useState([])

  const loadCommunities = async () => {
    try {
      const res = await api.getCommunities()
      setCommunities(res || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadCommunities() }, [])

  const handleAutoDetect = async () => {
    try {
      const res = await api.autoDetectCommunities()
      setCommunities(res || [])
    } catch (e) { console.error(e) }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    try {
      await api.createCommunity({
        name: name.trim(),
        community_type: type,
        tags: tag.trim() ? [tag.trim()] : [],
      })
      setName('')
      setTag('')
      loadCommunities()
    } catch (e) { console.error(e) }
  }

  const handleSelect = async (comm) => {
    setSelectedComm(comm)
    try {
      const sums = await api.getCommunitySummaries(comm.id)
      setSummaries(sums || [])
    } catch (e) { console.error(e) }
  }

  const handleGenerateSummary = async (commId) => {
    try {
      await api.generateCommunitySummary(commId, 'OVERVIEW')
      const sums = await api.getCommunitySummaries(commId)
      setSummaries(sums || [])
    } catch (e) { console.error(e) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button className="btn-primary" onClick={handleAutoDetect}>⚡ 自动检测逻辑社区 (按卷/剧情线)</button>
      </div>

      <form onSubmit={handleCreate} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          type="text"
          placeholder="社区名称 (如: 仙盟与各大门派)..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="CUSTOM">自定义社区</option>
          <option value="FACTION">阵营社区</option>
          <option value="PLOT_THREAD">剧情线社区</option>
          <option value="VOLUME">卷社区</option>
        </select>
        <input
          type="text"
          placeholder="标签 (可选)..."
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          style={{ width: '100px' }}
        />
        <button type="submit" className="btn-primary">➕ 创建社区</button>
      </form>

      <h4>逻辑社区列表 ({communities.length} 个)</h4>
      <div className="continuity-list" style={{ marginTop: '8px', marginBottom: '16px' }}>
        {communities.map((c) => (
          <div key={c.id} className={`continuity-card ${selectedComm?.id === c.id ? 'active' : ''}`} style={{ cursor: 'pointer' }} onClick={() => handleSelect(c)}>
            <div className="continuity-card-header">
              <span><strong>{c.name}</strong> <span className="badge gray">[{c.community_type}]</span></span>
              <span className={`badge ${c.status === 'ACTIVE' ? 'success' : 'warning'}`}>{c.status}</span>
            </div>
          </div>
        ))}
      </div>

      {selectedComm && (
        <div className="continuity-card">
          <div className="continuity-card-header">
            <strong>{selectedComm.name} - 社区摘要与派生缓存</strong>
            <button className="btn-small btn-primary" onClick={() => handleGenerateSummary(selectedComm.id)}>⚡ 生成/重建摘要</button>
          </div>
          <div style={{ marginTop: '8px' }}>
            {summaries.length === 0 && <p className="empty-state">该社区尚未生成摘要缓存</p>}
            {summaries.map((s) => (
              <div key={s.id} style={{ marginTop: '8px', fontSize: '13px', background: '#1c1f24', padding: '8px', borderRadius: '4px' }}>
                <span className="badge success">[{s.summary_type}]</span> (Tokens: {s.token_count})
                <p style={{ marginTop: '4px', whiteSpace: 'pre-wrap' }}>{s.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
