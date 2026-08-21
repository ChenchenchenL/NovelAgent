import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function LocationMovementManager() {
  const [locations, setLocations] = useState([])
  const [profiles, setProfiles] = useState([])
  const [locName, setLocName] = useState('')
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const [travelMode, setTravelMode] = useState('HORSE')
  const [minDur, setMinDur] = useState('60')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const [lRes, pRes] = await Promise.all([api.getLocations(), api.getTravelProfiles()])
      setLocations(lRes)
      setProfiles(pRes)
      if (lRes.length >= 2) {
        setFromId(lRes[0].id)
        setToId(lRes[1].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleAddLoc = async (e) => {
    e.preventDefault()
    if (!locName.trim()) return
    setLoading(true)
    try {
      await api.createLocation({ name: locName })
      setLocName('')
      await loadData()
    } finally {
      setLoading(false)
    }
  }

  const handleAddProfile = async (e) => {
    e.preventDefault()
    if (!fromId || !toId || fromId === toId) return alert('请选择不同的起点和终点')
    setLoading(true)
    try {
      await api.createTravelProfile({
        from_location_id: Number(fromId),
        to_location_id: Number(toId),
        travel_mode: travelMode,
        min_duration_minutes: Number(minDur) || 0,
      })
      await loadData()
    } finally {
      setLoading(false)
    }
  }

  const locMap = Object.fromEntries(locations.map(l => [l.id, l.name]))

  return (
    <div className="continuity-subpanel">
      <div className="inline-forms">
        <form onSubmit={handleAddLoc} className="continuity-form-inline">
          <input placeholder="新增地点名称 *" value={locName} onChange={e => setLocName(e.target.value)} required />
          <button type="submit" disabled={loading} className="btn-primary">添加地点</button>
        </form>
        <form onSubmit={handleAddProfile} className="continuity-form-inline">
          <select value={fromId} onChange={e => setFromId(e.target.value)}>{locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select>
          <span>→</span>
          <select value={toId} onChange={e => setToId(e.target.value)}>{locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select>
          <select value={travelMode} onChange={e => setTravelMode(e.target.value)}>
            <option value="WALK">步行 (WALK)</option>
            <option value="HORSE">骑马 (HORSE)</option>
            <option value="CARRIAGE">马车 (CARRIAGE)</option>
            <option value="BOAT">乘船 (BOAT)</option>
            <option value="TELEPORT">传送 (TELEPORT)</option>
          </select>
          <input type="number" placeholder="最短耗时(分)" value={minDur} onChange={e => setMinDur(e.target.value)} style={{ width: 90 }} />
          <button type="submit" disabled={loading} className="btn-primary">设置规则</button>
        </form>
      </div>
      <div className="continuity-list">
        {profiles.map(p => (
          <div key={p.id} className="continuity-card">
            <div className="continuity-card-header">
              <span>📍 <strong>{locMap[p.from_location_id] || p.from_location_id}</strong> → <strong>{locMap[p.to_location_id] || p.to_location_id}</strong></span>
              <span className="badge info">{p.travel_mode} : ≥ {p.min_duration_minutes} 分钟</span>
            </div>
          </div>
        ))}
        {profiles.length === 0 && <div className="empty-state">暂无时空移动规则</div>}
      </div>
    </div>
  )
}
