import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ImpactGraphViewer({ currentSceneId }) {
  const [summary, setSummary] = useState(null)
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [selectedNodeId, setSelectedNodeId] = useState('')
  const [propResult, setPropResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    try {
      const [sum, nList, eList] = await Promise.all([
        api.getProjectImpactSummary(),
        api.getImpactNodes(),
        api.getImpactEdges(),
      ])
      setSummary(sum)
      setNodes(nList)
      setEdges(eList)
      if (nList.length > 0 && !selectedNodeId) setSelectedNodeId(nList[0].id)
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadData() }, [currentSceneId])

  const handleSimulate = async () => {
    if (!selectedNodeId) return
    setLoading(true)
    try {
      const res = await api.propagateImpact({ changed_node_id: Number(selectedNodeId), change_type: 'MODIFIED' })
      setPropResult(res)
    } finally { setLoading(false) }
  }

  return (
    <div className="continuity-subpanel">
      {summary && (
        <div className="continuity-card" style={{ marginBottom: '12px' }}>
          <strong>Impact Graph 概览：</strong>
          <span className="badge">总节点: {summary.total_nodes}</span>
          <span className="badge gray">依赖边: {summary.total_edges}</span>
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <h4>影响节点列表 ({nodes.length})</h4>
          <div className="continuity-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {nodes.map(n => (
              <div key={n.id} className={`continuity-card ${Number(selectedNodeId) === n.id ? 'active' : ''}`} onClick={() => setSelectedNodeId(n.id)} style={{ cursor: 'pointer' }}>
                <div className="continuity-card-header">
                  <strong>#{n.id} {n.node_type}</strong>
                  <span className="badge gray">{n.entity_type || '全局'}</span>
                </div>
                <small>场景: #{n.scene_id || '无'} | 实体ID: #{n.entity_id || '无'}</small>
              </div>
            ))}
            {nodes.length === 0 && <div className="empty-state">暂无影响图节点</div>}
          </div>
        </div>
        <div>
          <h4>失效传播模拟器</h4>
          <div className="continuity-form" style={{ marginTop: '8px' }}>
            <select value={selectedNodeId} onChange={e => setSelectedNodeId(e.target.value)}>
              {nodes.map(n => <option key={n.id} value={n.id}>#{n.id} {n.node_type} ({n.entity_type})</option>)}
            </select>
            <button onClick={handleSimulate} disabled={loading || !selectedNodeId} className="btn-primary">
              {loading ? '传播计算中...' : '模拟失效传播'}
            </button>
          </div>
          {propResult && (
            <div className="continuity-card" style={{ marginTop: '12px' }}>
              <h5>传播结果:</h5>
              <p>受影响场景: <strong>{propResult.affected_scenes.join(', ') || '无'}</strong></p>
              <p>失效/待复核节点数: <strong>{propResult.stale_nodes.length}</strong></p>
              <div className="tag-row">
                {propResult.suggestions.map((s, idx) => <span key={idx} className="badge warning">{s}</span>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
