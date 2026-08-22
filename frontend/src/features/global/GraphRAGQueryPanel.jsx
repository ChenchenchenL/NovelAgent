import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function GraphRAGQueryPanel() {
  const [queryText, setQueryText] = useState('')
  const [queryType, setQueryType] = useState('MULTI_HOP')
  const [loading, setLoading] = useState(false)
  const [currentResult, setCurrentResult] = useState(null)
  const [history, setHistory] = useState([])

  const loadHistory = async () => {
    try {
      const res = await api.getGraphragQueries()
      setHistory(res || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadHistory() }, [])

  const handleQuery = async (e) => {
    e.preventDefault()
    if (!queryText.trim()) return
    setLoading(true)
    try {
      const res = await api.queryGraphrag({
        query_type: queryType,
        query_text: queryText.trim(),
        parameters: { max_hops: 4 },
      })
      setCurrentResult(res)
      loadHistory()
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleQuery} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <select value={queryType} onChange={(e) => setQueryType(e.target.value)}>
          <option value="MULTI_HOP">多跳关系分析 (MULTI_HOP)</option>
          <option value="CROSS_VOLUME">跨卷主题追踪 (CROSS_VOLUME)</option>
          <option value="GLOBAL_THEME">全书核心冲突 (GLOBAL_THEME)</option>
          <option value="FORESHADOW_NETWORK">伏笔网络全景 (FORESHADOW_NETWORK)</option>
          <option value="CHARACTER_ARC">人物成长轨迹 (CHARACTER_ARC)</option>
        </select>
        <input
          type="text"
          placeholder="输入全局查询问题 (如: 从林舟到玄机阁主的完整关系链)..."
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? '分析中...' : 'GraphRAG 查询'}
        </button>
      </form>

      {currentResult && (
        <div className="continuity-card" style={{ marginBottom: '16px', background: '#1c1936' }}>
          <div className="continuity-card-header">
            <strong>查询结果 ({currentResult.query_type}) - 耗时 {currentResult.duration_ms}ms (Tokens: {currentResult.token_cost})</strong>
            <span className="badge success">已关联 {currentResult.communities_used.length} 个社区</span>
          </div>
          <p style={{ marginTop: '8px', fontSize: '14px', whiteSpace: 'pre-wrap' }}>
            {currentResult.result?.answer || '无结果内容'}
          </p>
        </div>
      )}

      <h4>历史 GraphRAG 查询 ({history.length} 条)</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {history.map((h) => (
          <div key={h.id} className="continuity-card" style={{ cursor: 'pointer' }} onClick={() => setCurrentResult(h)}>
            <div className="continuity-card-header">
              <span><strong>{h.query_text}</strong> <span className="badge gray">[{h.query_type}]</span></span>
              <span className="badge success">{h.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
