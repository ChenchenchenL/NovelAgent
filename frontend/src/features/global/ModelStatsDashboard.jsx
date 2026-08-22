import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ModelStatsDashboard() {
  const [summary, setSummary] = useState(null)
  const [daily, setDaily] = useState([])
  const [byModel, setByModel] = useState({})

  const loadStats = async () => {
    try {
      const [s, d, m] = await Promise.all([
        api.getModelStatsSummary(),
        api.getModelStatsDaily(),
        api.getModelStatsByModel(),
      ])
      setSummary(s)
      setDaily(d || [])
      setByModel(m || {})
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadStats() }, [])

  const handleAggregate = async () => {
    try {
      await api.aggregateModelStats()
      loadStats()
    } catch (e) { console.error(e) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4>模型治理、Token 消耗与成本统计</h4>
        <button className="btn-small btn-primary" onClick={handleAggregate}>重新聚合今日统计</button>
      </div>

      {summary && (
        <div className="continuity-card" style={{ marginBottom: '16px' }}>
          <div className="continuity-card-header">
            <strong>全项目调用概览 (总调用: {summary.total_calls} 次)</strong>
            <span className="badge success">预估成本: ${summary.estimated_cost_usd}</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', display: 'flex', gap: '16px' }}>
            <span>成功: <strong>{summary.success_calls}</strong></span>
            <span>失败: <strong>{summary.failed_calls}</strong></span>
            <span>降级调用: <strong>{summary.degraded_calls}</strong> ({Math.round(summary.degradation_rate * 100)}%)</span>
            <span>总消耗 Tokens: <strong>{summary.total_tokens.toLocaleString()}</strong></span>
          </div>
        </div>
      )}

      <h4>按模型调用细分</h4>
      <div className="continuity-list" style={{ marginTop: '8px', marginBottom: '16px' }}>
        {Object.entries(byModel).map(([model, data]) => (
          <div key={model} className="continuity-card">
            <div className="continuity-card-header">
              <span><strong>{model}</strong> (调用: {data.calls} 次, 降级: {data.degraded} 次)</span>
              <span className="badge gray">Tokens: {data.tokens.toLocaleString()} (${data.cost})</span>
            </div>
          </div>
        ))}
      </div>

      <h4>每日调用明细</h4>
      <div className="continuity-list" style={{ marginTop: '8px' }}>
        {daily.map((d) => (
          <div key={d.id} className="continuity-card">
            <div className="continuity-card-header">
              <span>{d.date} - <strong>{d.model_name}</strong> [{d.task_type}]</span>
              <span className="badge success">{d.total_calls} 次 (平均 {d.avg_duration_ms}ms)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
