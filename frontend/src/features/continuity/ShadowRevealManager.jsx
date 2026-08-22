import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ShadowRevealManager({ currentSceneId }) {
  const [shadows, setShadows] = useState([])
  const [characters, setCharacters] = useState([])
  const [name, setName] = useState('')
  const [selectedShadowId, setSelectedShadowId] = useState(null)
  const [canonicalId, setCanonicalId] = useState('')
  const [evidence, setEvidence] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const [shRes, charRes] = await Promise.all([api.getShadowEntities(), api.getCharacters()])
      setShadows(shRes)
      setCharacters(charRes)
      if (charRes.length > 0) setCanonicalId(charRes[0].id)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createShadowEntity({ display_name: name })
      setName('')
      await loadData()
    } finally {
      setLoading(false)
    }
  }

  const handleReveal = async (shadowId) => {
    if (!canonicalId) return
    setErrorMsg('')
    try {
      await api.revealShadowEntity(shadowId, {
        canonical_character_id: Number(canonicalId),
        reveal_scene_id: currentSceneId || 1,
        evidence: evidence || '作者决议确认身份揭晓',
      })
      setSelectedShadowId(null)
      setEvidence('')
      await loadData()
    } catch (err) {
      setErrorMsg(err.message || '身份合并失败')
    }
  }

  const charMap = Object.fromEntries(characters.map(c => [c.id, c.name]))

  return (
    <div className="continuity-subpanel">
      {errorMsg && <div className="error-banner">{errorMsg}</div>}
      <form onSubmit={handleCreate} className="continuity-form">
        <input placeholder="马甲/影子身份名称 *" value={name} onChange={e => setName(e.target.value)} required />
        <button type="submit" disabled={loading} className="btn-primary">创建马甲实体</button>
      </form>
      <div className="continuity-list">
        {shadows.map(s => (
          <div key={s.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong>{s.display_name}</strong>
              <span className={`badge ${s.revealed ? 'success' : 'warning'}`}>{s.revealed ? '已揭晓' : '未揭晓'}</span>
            </div>
            {s.revealed ? (
              <div className="card-desc">真实身份: <strong>{charMap[s.canonical_character_id] || `人物#${s.canonical_character_id}`}</strong></div>
            ) : (
              <div className="action-row">
                {selectedShadowId === s.id ? (
                  <>
                    <select value={canonicalId} onChange={e => setCanonicalId(e.target.value)}>
                      {characters.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                    <input placeholder="揭晓证据/线索" value={evidence} onChange={e => setEvidence(e.target.value)} />
                    <button onClick={() => handleReveal(s.id)} className="btn-sm btn-primary">确认揭晓</button>
                    <button onClick={() => setSelectedShadowId(null)} className="btn-sm">取消</button>
                  </>
                ) : (
                  <button onClick={() => setSelectedShadowId(s.id)} className="btn-sm">进行身份关联</button>
                )}
              </div>
            )}
          </div>
        ))}
        {shadows.length === 0 && <div className="empty-state">暂无马甲实体</div>}
      </div>
    </div>
  )
}
