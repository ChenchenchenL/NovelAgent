import React from 'react'

export function AgentThoughtStream({ thoughtProcess }) {
  if (!thoughtProcess) return null

  const {
    grounding_fragments = 0,
    beats_status = '默认推进',
    quality_score = 92,
    cliches_flagged = 0,
    auto_extracted_claims = 0,
    duration_ms = 0,
  } = thoughtProcess

  return (
    <div style={{
      margin: '12px 0',
      padding: '10px 14px',
      background: '#13171e',
      border: '1px solid #242931',
      borderRadius: '6px',
      fontSize: '13px',
      color: '#cbd5e1',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <span><strong>推演自检与记忆状态</strong></span>
        <span className="badge success">质量评分: {quality_score}/100 ({duration_ms}ms)</span>
      </div>

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '6px', fontSize: '12px' }}>
        <span>上下文关联: <strong>{grounding_fragments} 条碎片</strong></span>
        <span>节拍推进: <strong>{beats_status}</strong></span>
        <span>套话检测: <strong>{cliches_flagged === 0 ? '无违规' : `${cliches_flagged} 处已修正`}</strong></span>
        <span>正典沉淀: <strong>+{auto_extracted_claims} 条新主张</strong></span>
      </div>
    </div>
  )
}
