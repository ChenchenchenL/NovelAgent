import React, { useState } from 'react'

export function AiCopilotTab({
  generating,
  statusText,
  streamingText,
  runs,
  onStartGeneration,
  onCancelGeneration,
  onApplyStreaming,
}) {
  const [taskType, setTaskType] = useState('paragraph_generation')
  const [tier, setTier] = useState('T3')
  const [instruction, setInstruction] = useState('')
  const [temperature, setTemperature] = useState(0.7)

  const handleGenerate = (e) => {
    e.preventDefault()
    onStartGeneration({
      task_type: taskType,
      tier,
      instruction: instruction.trim() || '承接前文继续当前场景写作',
      parameters: { temperature: parseFloat(temperature), max_tokens: 2000 },
    })
  }

  return (
    <div className="inspector-tab-content copilot-tab">
      <form onSubmit={handleGenerate} className="copilot-form">
        <div className="form-group-compact">
          <label>推演任务</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
            <option value="paragraph_generation">段落续写 (T3 写作)</option>
            <option value="beat_plan">节拍规划 (T2 规划)</option>
            <option value="scene_summary">场景摘要提取 (T1 抽取)</option>
            <option value="continuity_check">连续性自检 (T2 检查)</option>
          </select>
        </div>

        <div className="form-row-compact">
          <div className="form-group-compact flex-1">
            <label>模型层级</label>
            <select value={tier} onChange={(e) => setTier(e.target.value)}>
              <option value="T3">T3 旗舰写作</option>
              <option value="T2">T2 中型规划</option>
              <option value="T1">T1 快速抽取</option>
            </select>
          </div>
          <div className="form-group-compact flex-1">
            <label>发散度: {temperature}</label>
            <input
              type="range" min="0.1" max="1.5" step="0.1"
              value={temperature} onChange={(e) => setTemperature(e.target.value)}
            />
          </div>
        </div>

        <div className="form-group-compact">
          <label>写作提示 / 约束</label>
          <textarea
            rows={3}
            placeholder="例如：描写二人剑拔弩张的对话，注意保持主角沉着性格..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
          />
        </div>

        <div className="copilot-form-actions">
          {generating ? (
            <button type="button" className="btn-cancel-gen" onClick={onCancelGeneration}>
              中止推演
            </button>
          ) : (
            <button type="submit" className="btn-start-gen">
              开始推演
            </button>
          )}
        </div>
      </form>

      {(generating || streamingText) && (
        <div className="copilot-stream-box">
          <div className="stream-header">
            <span className="stream-status">{statusText || (generating ? '模型推演中...' : '推演完成')}</span>
            {!generating && streamingText && onApplyStreaming && (
              <button className="btn-apply-stream" onClick={() => onApplyStreaming(streamingText)}>
                插入草稿
              </button>
            )}
          </div>
          <div className="stream-body">{streamingText}</div>
        </div>
      )}

      {runs && runs.length > 0 && (
        <div className="copilot-task-history">
          <div className="history-header">推演记录 ({runs.length})</div>
          <div className="history-list">
            {runs.slice(0, 5).map((r) => (
              <div key={r.id} className="history-item">
                <span>#{r.id} [{r.model_tier}] {r.task_type}</span>
                <span className={`badge-sm status-${(r.status || '').toLowerCase()}`}>{r.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
