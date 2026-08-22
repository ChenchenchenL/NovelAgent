import React, { useState, useEffect } from 'react'
import { api } from '../../../api/client'

export function CharacterQuickTab() {
  const [characters, setCharacters] = useState([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [traits, setTraits] = useState('')
  const [loading, setLoading] = useState(false)

  const loadChars = async () => {
    try {
      const res = await api.getCharacters()
      setCharacters(res || [])
    } catch { setCharacters([]) }
  }

  useEffect(() => { loadChars() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      const traitList = traits.trim() ? traits.split(/[,， ]+/).filter(Boolean) : []
      await api.createCharacter({
        name: name.trim(),
        background: desc.trim(),
        core_traits: traitList,
      })
      setName('')
      setDesc('')
      setTraits('')
      await loadChars()
    } catch (err) {
      alert(`添加角色失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="inspector-tab-content">
      <div className="ai-cockpit-card">
        <span className="cockpit-title">添加新角色到全书设定</span>
        <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <input
            placeholder="角色姓名 (必填，例如：林舟)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            placeholder="核心身份与背景 (例如：万仙宗底层外门维修工)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
          <input
            placeholder="性格特征标签 (用空格或逗号隔开，例如：机智 隐忍)"
            value={traits}
            onChange={(e) => setTraits(e.target.value)}
          />
          <button type="submit" className="btn-blue" disabled={loading} style={{ width: '100%', height: '34px' }}>
            {loading ? '正在保存...' : '添加角色'}
          </button>
        </form>
      </div>

      <div className="beats-list">
        {characters.length === 0 ? (
          <div className="empty-hint">暂无角色档案，AI 推演大纲时将自动生成核心人物关系网</div>
        ) : (
          characters.map((c) => (
            <div key={c.id} className="beat-card">
              <div className="beat-card-top">
                <strong style={{ fontSize: '13.5px', color: '#09090b' }}>{c.name}</strong>
                {c.aliases?.length > 0 && (
                  <span className="req-tag">{c.aliases.join(', ')}</span>
                )}
              </div>
              {c.core_traits?.length > 0 && (
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                  {c.core_traits.map((t, idx) => (
                    <span key={idx} className="req-tag" style={{ background: '#eff6ff', color: '#1d4ed8' }}>{t}</span>
                  ))}
                </div>
              )}
              {c.background && (
                <p style={{ fontSize: '12px', color: '#52525b', marginTop: '6px', lineHeight: '1.5' }}>
                  {c.background}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
