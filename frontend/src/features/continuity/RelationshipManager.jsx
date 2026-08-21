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
      setCharacters(chars)
      setRelationships(rels)
      if (chars.length >= 2) {
        setSubId(chars[0].id)
        setObjId(chars[1].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!subId || !objId || subId === objId) return alert('请选择不同的主体与客体')
    if (!currentSceneId) return alert('请先在左侧目录选中一个场景作为当前上下文')
    setLoading(true)
    try {
      await api.createRelationship({
        subject_character_id: Number(subId),
        object_character_id: Number(objId),
        relationship_type: relType,
        scene_id: currentSceneId,
        evidence,
        confirmed: true,
      })
      setEvidence('')
      await loadData()
    } catch (err) {
      alert(err.message || '记录失败')
    } finally {
      setLoading(false)
    }
  }

  const charMap = Object.fromEntries(characters.map(c => [c.id, c.name]))

  return (
    <div className="continuity-subpanel">
      {!currentSceneId && <div className="warning-banner">提示：当前未选中场景，添加关系需绑定上下文场景。</div>}
      <form onSubmit={handleAdd} className="continuity-form">
        <select value={subId} onChange={e => setSubId(e.target.value)}>
          {characters.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={relType} onChange={e => setRelType(e.target.value)}>
          <option value="ALLY">盟友 (ALLY)</option>
          <option value="ENEMY">敌人 (ENEMY)</option>
          <option value="TRUSTS">信任 (TRUSTS)</option>
          <option value="DISTRUSTS">怀疑 (DISTRUSTS)</option>
          <option value="LOVES">爱慕 (LOVES)</option>
          <option value="HATES">仇恨 (HATES)</option>
          <option value="BETRAYS">背叛 (BETRAYS)</option>
        </select>
        <select value={objId} onChange={e => setObjId(e.target.value)}>
          {characters.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input placeholder="关系变化证据 / 剧情" value={evidence} onChange={e => setEvidence(e.target.value)} />
        <button type="submit" disabled={loading || !currentSceneId} className="btn-primary">记录关系</button>
      </form>
      <div className="continuity-list">
        {relationships.map(r => (
          <div key={r.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>{charMap[r.subject_character_id] || r.subject_character_id}</strong> → <code>{r.relationship_type}</code> → <strong>{charMap[r.object_character_id] || r.object_character_id}</strong></span>
              <span className="badge">已确认</span>
            </div>
          </div>
        ))}
        {relationships.length === 0 && <div className="empty-state">暂无关系数据</div>}
      </div>
    </div>
  )
}
