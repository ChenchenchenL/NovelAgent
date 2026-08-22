import React, { useState } from 'react'
import { api } from '../../api/client'

export function VectorSearchPanel() {
  const [queryText, setQueryText] = useState('')
  const [results, setResults] = useState([])
  const [topK, setTopK] = useState(10)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!queryText.trim()) return
    setLoading(true)
    try {
      const res = await api.searchVector({ query_text: queryText.trim(), top_k: topK })
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
          placeholder="输入场景情节、语义或文风描述..."
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={topK} onChange={(e) => setTopK(Number(e.target.value))}>
          <option value={5}>Top 5</option>
          <option value={10}>Top 10</option>
          <option value={20}>Top 20</option>
        </select>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? '检索中...' : '向量检索'}
        </button>
      </form>

      <div className="continuity-list">
        {results.length === 0 && !loading && (
          <div className="empty-state">输入语义描述检索相似场景与文风片段</div>
        )}
        {results.map((item) => (
          <div key={item.id} className="continuity-card">
            <div className="continuity-card-header">
              <span>
                <span className="badge gray">{item.doc_type}</span>{' '}
                <strong>场景/来源 #{item.source_id} (v{item.source_version})</strong>
              </span>
              <span className="badge success">
                相似度: {item.similarity}
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
