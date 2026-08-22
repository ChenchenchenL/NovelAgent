import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ClicheBlacklistManager() {
  const [cliches, setCliches] = useState([])
  const [pattern, setPattern] = useState('')
  const [patternType, setPatternType] = useState('EXACT')
  const [category, setCategory] = useState('GENERAL')
  const [severity, setSeverity] = useState('WARNING')
  const [scanText, setScanText] = useState('')
  const [scanResults, setScanResults] = useState([])

  const loadCliches = async () => {
    try {
      const res = await api.getClicheBlacklist()
      setCliches(res || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadCliches() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!pattern.trim()) return
    try {
      await api.createClicheEntry({
        pattern: pattern.trim(),
        pattern_type: patternType,
        category,
        severity,
      })
      setPattern('')
      loadCliches()
    } catch (e) { console.error(e) }
  }

  const handleDelete = async (id) => {
    try {
      await api.deleteClicheEntry(id)
      loadCliches()
    } catch (e) { console.error(e) }
  }

  const handleScan = async () => {
    if (!scanText.trim()) return
    try {
      const res = await api.scanCliches({ text: scanText.trim() })
      setScanResults(res || [])
    } catch (e) { console.error(e) }
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleAdd} style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <input
          type="text"
          placeholder="套话/口癖 (如: 不知不觉中, 事情并没有那么简单)..."
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={patternType} onChange={(e) => setPatternType(e.target.value)}>
          <option value="EXACT">精确匹配</option>
          <option value="REGEX">正则匹配</option>
          <option value="FUZZY">模糊匹配</option>
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="GENERAL">通用套话</option>
          <option value="EMPTY_OPENING">空洞开场</option>
          <option value="GENERIC_TRANSITION">泛化转折</option>
          <option value="MODEL_QUIRK">模型口癖</option>
        </select>
        <button type="submit" className="btn-primary">加入黑名单</button>
      </form>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          type="text"
          placeholder="输入测试文本扫描套话..."
          value={scanText}
          onChange={(e) => setScanText(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn-small" onClick={handleScan}>扫描套话</button>
      </div>

      {scanResults.length > 0 && (
        <div className="continuity-card" style={{ marginBottom: '16px', background: '#251a24' }}>
          <h4>扫描命中 ({scanResults.length} 处)</h4>
          {scanResults.map((r, i) => (
            <div key={i} style={{ marginTop: '4px', fontSize: '13px' }}>
              <span className="badge warning">{r.severity}</span> {r.description}
            </div>
          ))}
        </div>
      )}

      <h4>已配置套话黑名单 ({cliches.length} 条)</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {cliches.map((c) => (
          <div key={c.id} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>{c.pattern}</strong> <span className="badge gray">[{c.pattern_type}] {c.category}</span></span>
              <button className="btn-small btn-danger" onClick={() => handleDelete(c.id)}>删除</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
