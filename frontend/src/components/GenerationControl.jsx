import React, { useState } from 'react'

export function GenerationControl({ generating, onGenerate, onCancel }) {
  const [taskType, setTaskType] = useState('paragraph_generation')
  const [tier, setTier] = useState('T3')
  const [instruction, setInstruction] = useState('')
  const [temperature, setTemperature] = useState(0.7)

  const handleSubmit = (e) => {
    e.preventDefault()
    onGenerate({
      task_type: taskType,
      tier,
      instruction,
      parameters: {
        temperature: parseFloat(temperature),
        max_tokens: 2000,
      },
    })
  }

  return (
    <div className="panel generation-panel">
      <div className="panel-title">辅助推演控制台</div>
      <form onSubmit={handleSubmit} className="gen-form">
        <div className="form-group">
          <label>推演任务类型</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value)} disabled={generating}>
            <option value="paragraph_generation">段落续写 (T3 旗舰写作)</option>
            <option value="beat_plan">节拍规划 (T2 逻辑规划)</option>
            <option value="scene_summary">场景摘要 (T1 快速分析)</option>
            <option value="continuity_check">连续性自检 (T2 规则验证)</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>模型分级</label>
            <select value={tier} onChange={(e) => setTier(e.target.value)} disabled={generating}>
              <option value="T3">T3 旗舰写作</option>
              <option value="T2">T2 逻辑规划</option>
              <option value="T1">T1 快速抽取</option>
            </select>
          </div>
          <div className="form-group">
            <label>发散度: {temperature}</label>
            <input
              type="range" min="0.1" max="1.5" step="0.1"
              value={temperature} onChange={(e) => setTemperature(e.target.value)} disabled={generating}
            />
          </div>
        </div>

        <div className="form-group">
          <label>写作提示 / 约束要求</label>
          <textarea
            rows={3} placeholder="输入具体的行文要求、剧情转向或人物情感基调..."
            value={instruction} onChange={(e) => setInstruction(e.target.value)} disabled={generating}
          />
        </div>

        <div className="form-actions">
          {generating ? (
            <button type="button" className="btn-danger" onClick={onCancel}>中止推演</button>
          ) : (
            <button type="submit" className="primary">开始推演</button>
          )}
        </div>
      </form>
    </div>
  )
}
