import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function CharacterManager() {
  const [characters, setCharacters] = useState([])
  const [name, setName] = useState('')
  const [aliasStr, setAliasStr] = useState('')
  const [background, setBackground] = useState('')
  const [loading, setLoading] = useState(false)

  const loadChars = async () => {
    try {
      const res = await api.getCharacters()
      setCharacters(res)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadChars() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      const aliases = aliasStr ? aliasStr.split(/[,，]/).map(s => s.trim()).filter(Boolean) : []
      await api.createCharacter({ name, aliases, background })
      setName('')
      setAliasStr('')
      setBackground('')
      await loadChars()
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该人物档案？')) return
    await api.deleteCharacter(id)
    await loadChars()
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreate} className="continuity-form">
        <input placeholder="人物姓名 *" value={name} onChange={e => setName(e.target.value)} required />
        <input placeholder="别名/马甲 (逗号分隔)" value={aliasStr} onChange={e => setAliasStr(e.target.value)} />
        <input placeholder="背景简介" value={background} onChange={e => setBackground(e.target.value)} />
        <button type="submit" disabled={loading} className="btn-primary">添加人物</button>
      </form>
      <div className="continuity-list">
        {characters.map(c => (
          <div key={c.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong>{c.name}</strong>
              <button onClick={() => handleDelete(c.id)} className="btn-sm btn-danger">删除</button>
            </div>
            {c.aliases?.length > 0 && <div className="tag-row">{c.aliases.map(a => <span key={a} className="badge">{a}</span>)}</div>}
            {c.background && <p className="card-desc">{c.background}</p>}
          </div>
        ))}
        {characters.length === 0 && <div className="empty-state">暂无人物档案</div>}
      </div>
    </div>
  )
}
