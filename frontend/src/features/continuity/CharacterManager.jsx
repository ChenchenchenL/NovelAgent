import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function CharacterManager() {
  const [characters, setCharacters] = useState([])
  const [name, setName] = useState('')
  const [aliasStr, setAliasStr] = useState('')
  const [background, setBackground] = useState('')
  const [traits, setTraits] = useState('')
  const [loading, setLoading] = useState(false)

  const loadChars = async () => {
    try {
      const res = await api.getCharacters()
      setCharacters(res || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadChars() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      const aliases = aliasStr ? aliasStr.split(/[,，]/).map(s => s.trim()).filter(Boolean) : []
      const traitList = traits ? traits.split(/[,， ]+/).map(s => s.trim()).filter(Boolean) : []
      await api.createCharacter({ name: name.trim(), aliases, background: background.trim(), core_traits: traitList })
      setName(''); setAliasStr(''); setBackground(''); setTraits('')
      await loadChars()
    } finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该人物档案？')) return
    await api.deleteCharacter(id)
    await loadChars()
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreate} className="continuity-form-card">
        <span style={{ fontSize: '13px', fontWeight: 650, color: '#09090b' }}>添加新人物档案</span>
        <div className="continuity-form-row">
          <input placeholder="人物姓名 * (例如: 林舟)" value={name} onChange={e => setName(e.target.value)} required />
          <input placeholder="别名/称号/马甲 (逗号分隔)" value={aliasStr} onChange={e => setAliasStr(e.target.value)} />
          <input placeholder="性格特质 (例如: 隐忍 机敏)" value={traits} onChange={e => setTraits(e.target.value)} />
        </div>
        <input placeholder="人物身份背景与核心动机简介" value={background} onChange={e => setBackground(e.target.value)} />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={loading} className="btn-blue">添加人物</button>
        </div>
      </form>

      <div className="continuity-cards-grid">
        {characters.map(c => (
          <div key={c.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong style={{ fontSize: '14px', color: '#09090b' }}>{c.name}</strong>
              <button onClick={() => handleDelete(c.id)} className="mini-btn" style={{ color: '#dc2626' }}>删除</button>
            </div>
            {c.aliases?.length > 0 && (
              <div className="tag-row">{c.aliases.map(a => <span key={a} className="badge gray">{a}</span>)}</div>
            )}
            {c.core_traits?.length > 0 && (
              <div className="tag-row">{c.core_traits.map(t => <span key={t} className="badge blue">{t}</span>)}</div>
            )}
            {c.background && <p className="card-desc" style={{ marginTop: '4px' }}>{c.background}</p>}
          </div>
        ))}
      </div>
      {characters.length === 0 && <div className="empty-state">暂无人物档案，可通过上方表单或 AI 全书推演生成</div>}
    </div>
  )
}
