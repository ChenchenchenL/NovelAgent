import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function KgBrowserPanel() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [srcNode, setSrcNode] = useState('')
  const [dstNode, setDstNode] = useState('')
  const [path, setPath] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [n, e] = await Promise.all([api.getKgNodes(), api.getKgEdges()])
      setNodes(n || [])
      setEdges(e || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  const handleQueryPath = async () => {
    if (!srcNode || !dstNode) return
    try {
      const p = await api.queryKgPath({ source_node_id: Number(srcNode), target_node_id: Number(dstNode), max_hops: 4 })
      setPath(p || [])
    } catch (err) { console.error(err) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '16px' }}>
        <select value={srcNode} onChange={(e) => setSrcNode(e.target.value)} style={{ flex: 1 }}>
          <option value="">选择起点实体...</option>
          {nodes.map((n) => <option key={n.id} value={n.id}>[{n.node_type}] {n.name}</option>)}
        </select>
        <span>➡️</span>
        <select value={dstNode} onChange={(e) => setDstNode(e.target.value)} style={{ flex: 1 }}>
          <option value="">选择终点实体...</option>
          {nodes.map((n) => <option key={n.id} value={n.id}>[{n.node_type}] {n.name}</option>)}
        </select>
        <button className="btn-primary" onClick={handleQueryPath}>查找路径</button>
      </div>

      {path && (
        <div className="continuity-card" style={{ marginBottom: '16px', background: '#252830' }}>
          <h4>🔗 多跳关系路径 ({path.length} 跳)</h4>
          {path.length === 0 ? <p>未发现有效连接路径</p> : (
            <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {path.map((step, idx) => (
                <span key={idx} className="badge gray">
                  节点#{step.from_node_id} --[{step.edge_type}]--&gt; 节点#{step.to_node_id}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <h4>KG 图投影统计 (节点: {nodes.length}, 边: {edges.length})</h4>
      <div className="continuity-list" style={{ marginTop: '10px' }}>
        {edges.slice(0, 15).map((e) => (
          <div key={e.id} className="continuity-card">
            <span><strong>{e.edge_type}</strong> (节点#{e.source_node_id} ➔ 节点#{e.target_node_id})</span>
            <span className="badge success">{e.modality}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
