import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function IndexManagerPanel() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [rebuilding, setRebuilding] = useState(false)

  const loadStatus = async () => {
    setLoading(true)
    try {
      const res = await api.getIndexesStatus()
      setStatus(res)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadStatus() }, [])

  const handleRebuildAll = async () => {
    setRebuilding(true)
    try {
      await api.rebuildAllIndexes()
      await loadStatus()
    } catch (e) { console.error(e) }
    finally { setRebuilding(false) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4>派生索引与缓存状态</h4>
        <button className="btn-primary" onClick={handleRebuildAll} disabled={rebuilding}>
          {rebuilding ? '重建中...' : '🔄 从正典一键全量重建'}
        </button>
      </div>

      {status && (
        <div className="continuity-list">
          <div className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>FTS5 全文索引</strong> ({status.fts.count} 篇)</span>
              <span className={`badge ${status.fts.status === 'HEALTHY' ? 'success' : 'warning'}`}>{status.fts.status}</span>
            </div>
          </div>
          <div className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>本地向量索引</strong> ({status.vector.count} 条)</span>
              <span className={`badge ${status.vector.status === 'HEALTHY' ? 'success' : 'warning'}`}>{status.vector.status}</span>
            </div>
          </div>
          <div className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>关系表 KG 投影</strong> (节点: {status.kg.nodes_count}, 边: {status.kg.edges_count})</span>
              <span className={`badge ${status.kg.status === 'HEALTHY' ? 'success' : 'warning'}`}>{status.kg.status}</span>
            </div>
          </div>
          <div className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>H-RAG 多层摘要</strong> ({status.summaries.count} 份)</span>
              <span className={`badge ${status.summaries.status === 'HEALTHY' ? 'success' : 'warning'}`}>{status.summaries.status}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
