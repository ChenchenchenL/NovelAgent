import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function RelationshipManager({ currentSceneId }) {
  const [characters, setCharacters] = useState([])
  const [relationships, setRelationships] = useState([])
  const [subId, setSubId] = useState('')
  const [objId, setObjId] = useState('')
  const [relType, setRelType] = useState('ALLY')
  const [evidence, setEvidence] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const [chars, rels] = await Promise.all([api.getCharacters(), api.getCurrentRelationships()])
      setCharacters(chars || [])
      setRelationships(rels || [])
      if (chars?.length >= 2) { setSubId(chars[0].id); setObjId(chars[1].id) }
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!subId || !objId || subId === objId) return alert('请选择不同的人物')
    setLoading(true)
    try {
      await api.createRelationship({
        subject_character_id: Number(subId), object_character_id: Number(objId),
        relationship_type: relType, scene_id: currentSceneId || undefined,
        evidence: evidence.trim(), confirmed: true,
      })
      setEvidence(''); await loadData()
    } catch (err) { alert(err.message || '记录失败') }
    finally { setLoading(false) }
  }

  const charMap = Object.fromEntries(characters.map(c => [c.id, c.name]))
  const relLabels = { ALLY: '盟友', ENEMY: '宿敌/对手', TRUSTS: '信任', DISTRUSTS: '怀疑', LOVES: '爱慕', HATES: '仇视', BETRAYS: '背叛/决裂' }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleAdd} className="continuity-form-card">
        <span style={{ fontSize: '13px', fontWeight: 650, color: '#09090b' }}>添加人物羁绊与关系</span>
        <div className="continuity-form-row">
          <select value={subId} onChange={e => setSubId(e.target.value)}>
            {characters.map(c => <option key={c.id} value={c.id}>人物A：{c.name}</option>)}
          </select>
          <select value={relType} onChange={e => setRelType(e.target.value)}>
            <option value="ALLY">盟友 / 同伴 (ALLY)</option>
            <option value="ENEMY">宿敌 / 对立 (ENEMY)</option>
            <option value="TRUSTS">托付 / 信任 (TRUSTS)</option>
            <option value="DISTRUSTS">试探 / 怀疑 (DISTRUSTS)</option>
            <option value="LOVES">情愫 / 爱慕 (LOVES)</option>
            <option value="HATES">仇恨 / 宿怨 (HATES)</option>
            <option value="BETRAYS">反目 / 背叛 (BETRAYS)</option>
          </select>
          <select value={objId} onChange={e => setObjId(e.target.value)}>
            {characters.map(c => <option key={c.id} value={c.id}>人物B：{c.name}</option>)}
          </select>
        </div>
        <input placeholder="关系变化契机或剧情描述 (可选)" value={evidence} onChange={e => setEvidence(e.target.value)} />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={loading} className="btn-blue">记录人物关系</button>
        </div>
      </form>

      <div className="continuity-cards-grid">
        {relationships.map(r => (
          <div key={r.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong style={{ fontSize: '13.5px', color: '#09090b' }}>
                {charMap[r.subject_character_id] || '人物A'}
                <span style={{ margin: '0 6px', color: '#2563eb', fontWeight: 'normal' }}>[{relLabels[r.relationship_type] || r.relationship_type}]</span>
                {charMap[r.object_character_id] || '人物B'}
              </strong>
            </div>
            {r.evidence && <p className="card-desc" style={{ marginTop: '4px' }}>{r.evidence}</p>}
          </div>
        ))}
      </div>
      {relationships.length === 0 && <div className="empty-state">暂无人物关系记录</div>}
    </div>
  )
}
