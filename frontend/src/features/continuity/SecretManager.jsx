import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function SecretManager({ currentSceneId }) {
  const [secrets, setSecrets] = useState([])
  const [characters, setCharacters] = useState([])
  const [name, setName] = useState('')
  const [content, setContent] = useState('')
  const [knowerId, setKnowerId] = useState('')
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const [secRes, charRes] = await Promise.all([api.getSecrets(), api.getCharacters()])
      setSecrets(secRes)
      setCharacters(charRes)
      if (charRes.length > 0) setKnowerId(charRes[0].id)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim() || !content.trim()) return
    if (!currentSceneId) return alert('请先在左侧目录选中一个场景作为当前上下文')
    setLoading(true)
    try {
      const known_by = knowerId ? [{ character_id: Number(knowerId), known_since_scene_id: currentSceneId }] : []
      await api.createSecret({
        secret_name: name,
        secret_content: content,
        created_scene_id: currentSceneId,
        known_by,
      })
      setName('')
      setContent('')
      await loadData()
    } catch (err) {
      alert(err.message || '创建秘密失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该叙事秘密？')) return
    await api.deleteSecret(id)
    await loadData()
  }

  const charMap = Object.fromEntries(characters.map(c => [c.id, c.name]))

  return (
    <div className="continuity-subpanel">
      {!currentSceneId && <div className="warning-banner">提示：当前未选中场景，添加秘密需绑定上下文场景。</div>}
      <form onSubmit={handleCreate} className="continuity-form">
        <input placeholder="秘密名称 *" value={name} onChange={e => setName(e.target.value)} required />
        <input placeholder="秘密内容 *" value={content} onChange={e => setContent(e.target.value)} required />
        <select value={knowerId} onChange={e => setKnowerId(e.target.value)}>
          <option value="">初始知情人 (可选)</option>
          {characters.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button type="submit" disabled={loading || !currentSceneId} className="btn-primary">新增秘密</button>
      </form>
      <div className="continuity-list">
        {secrets.map(s => (
          <div key={s.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong>🔒 {s.secret_name}</strong>
              <button onClick={() => handleDelete(s.id)} className="btn-icon danger">✕</button>
            </div>
            <p className="card-desc">{s.secret_content}</p>
            <div className="tag-row">
              <span className="badge-label">知情者:</span>
              {(s.known_by || []).map(k => (
                <span key={k.character_id} className="badge success">{charMap[k.character_id] || `人物#${k.character_id}`}</span>
              ))}
              {(!s.known_by || s.known_by.length === 0) && <span className="badge gray">无人知晓</span>}
            </div>
          </div>
        ))}
        {secrets.length === 0 && <div className="empty-state">暂无叙事秘密</div>}
      </div>
    </div>
  )
}
