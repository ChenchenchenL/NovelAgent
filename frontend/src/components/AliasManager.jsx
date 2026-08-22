import React, { useState } from 'react'
import { useAliases } from '../hooks/useAliases'

export function AliasManager({ onClose }) {
  const { aliases, loading, addAlias, removeAlias } = useAliases()
  const [canonical, setCanonical] = useState('')
  const [alias, setAlias] = useState('')
  const [aliasType, setAliasType] = useState('informal')

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!canonical.trim() || !alias.trim()) return
    await addAlias(canonical.trim(), alias.trim(), aliasType)
    setCanonical('')
    setAlias('')
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content alias-manager-modal">
        <div className="alias-manager-header">
          <h3>实体与人物别名管理库</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <form className="alias-add-form" onSubmit={handleAdd}>
          <input
            value={alias}
            placeholder="别名/昵称/代号 (如: 阿明)"
            onChange={(e) => setAlias(e.target.value)}
          />
          <span>映射到正典名:</span>
          <input
            value={canonical}
            placeholder="正典标准名 (如: 王明)"
            onChange={(e) => setCanonical(e.target.value)}
          />
          <select value={aliasType} onChange={(e) => setAliasType(e.target.value)}>
            <option value="informal">昵称/外号</option>
            <option value="shadow_title">影子身份</option>
            <option value="kodename">代号</option>
            <option value="penname">笔名/化名</option>
          </select>
          <button type="submit" disabled={loading} className="btn-primary">添加映射</button>
        </form>

        <div className="alias-list">
          {aliases.length === 0 ? (
            <div className="empty">暂无别名映射规则</div>
          ) : (
            aliases.map((item) => (
              <div key={item.id} className="alias-item">
                <span className="alias-tag">{item.alias_name}</span>
                <span className="alias-arrow">-&gt;</span>
                <strong className="canonical-tag">{item.canonical_name}</strong>
                <span className="alias-type-badge">[{item.alias_type}]</span>
                <button className="btn-del-alias" onClick={() => removeAlias(item.id)}>删除</button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
