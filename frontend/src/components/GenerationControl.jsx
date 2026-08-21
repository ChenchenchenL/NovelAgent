import React, { useState } from 'react'

export function GenerationControl({ onGenerate, generating, disabled }) {
  const [open, setOpen] = useState(false)
  const [taskType, setTaskType] = useState('paragraph_generation')
  const [tier, setTier] = useState('T3')
  const [instruction, setInstruction] = useState('')
  const [temperature, setTemperature] = useState(0.7)

  const handleSubmit = (e) => {
    e.preventDefault()
    onGenerate({
      task_type: taskType,
      tier,
      instruction: instruction.trim() || '继续当前场景创作',
      parameters: { temperature: parseFloat(temperature), max_tokens: 2000 },
    })
    setOpen(false)
  }

  return (
    <div className="generation-control-wrap">
      <button
        className="btn-ai-generate"
        disabled={disabled || generating}
        onClick={() => setOpen(true)}
      >
        {generating ? '生成中...' : '✨ AI 辅助创作'}
      </button>

      {open && (
        <div className="modal-overlay">
          <div className="modal-content generation-modal">
            <h3>AI 辅助创作配置</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>任务类型</label>
                <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
                  <option value="paragraph_generation">段落续写 (T3)</option>
                  <option value="scene_summary">场景摘要 (T1)</option>
                  <option value="beat_plan">节拍规划 (T2)</option>
                  <option value="continuity_check">冲突检查 (T2)</option>
                </select>
              </div>

              <div className="form-group">
                <label>模型分级 (Tier)</label>
                <select value={tier} onChange={(e) => setTier(e.target.value)}>
                  <option value="T3">T3 - 深度写作模型</option>
                  <option value="T2">T2 - 逻辑规划模型</option>
                  <option value="T1">T1 - 快速抽取模型</option>
                </select>
              </div>

              <div className="form-group">
                <label>创作指令 / 续写提示</label>
                <textarea
                  rows={3}
                  value={instruction}
                  placeholder="例如：描写二人剑拔弩张的对话，注意保持主角沉着性格..."
                  onChange={(e) => setInstruction(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>采样温度 (Creativity): {temperature}</label>
                <input
                  type="range"
                  min="0.1"
                  max="1.5"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setOpen(false)}>
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  开始生成
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
