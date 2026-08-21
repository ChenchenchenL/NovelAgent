import React, { useState } from 'react'
import { api } from '../../api/client'

export function FtsSearchPanel() {
  const [query, setQuery] = useState('')
  const [docType, setDocType] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const params = { query: query.trim() }
      if (docType) params.doc_type = docType
      const res = await api.searchFts(params)
      setResults(res || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          type="text"
          placeholder="输入专名、原句或关键词搜索全文..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={docType} onChange={(e) => setDocType(e.target.value)}>
          <option value="">全部类型</option>
          <option value="SCENE">场景原文 (SCENE)</option>
          <option value="CLAIM">结构化主张 (CLAIM)</option>
          <option value="SUMMARY">摘要 (SUMMARY)</option>
        </select>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? '搜索中...' : '🔍 检索'}
        </button>
      </form>

      <div className="continuity-list">
        {results.length === 0 && !loading && (
          <div className="empty-state">暂无搜索结果或未发起检索</div>
        )}
        {results.map((item) => (
          <div key={item.id} className="continuity-card">
            <div className="continuity-card-header">
              <span>
                <span className="badge gray">{item.doc_type}</span>{' '}
                <strong>来源 #{item.source_id} (v{item.source_version})</strong>
              </span>
              <span className={`badge ${item.confirmed ? 'success' : 'warning'}`}>
                {item.modality}
              </span>
            </div>
            <p style={{ marginTop: '8px', fontSize: '13px', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
              {item.content}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
