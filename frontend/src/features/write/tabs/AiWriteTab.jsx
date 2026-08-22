import React, { useState } from 'react'
import { api } from '../../../api/client'
import { AgentThoughtStream } from '../../agent/AgentThoughtStream'

export function AiWriteTab({
  scene,
  onApplyStreaming,
  onSceneContentUpdated,
  onAdvanceCompleted,
}) {
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [thoughtProcess, setThoughtProcess] = useState(null)

  const handleAutoWriteScene = async () => {
    if (!scene?.id) return alert('请先在左侧选择一个场景')
    setLoading(true)
    setStatusText('AI 正在参考全书大纲与前文，自动撰写本场正文...')
    setStreamingText('')
    try {
      const res = await api.autoWriteScene({
        scene_id: scene.id,
        auto_extract: true,
        guidance: instruction.trim() || undefined,
      })
      setThoughtProcess(res.thought_process)
      if (res.content) {
        setStreamingText(res.content)
        if (onSceneContentUpdated) onSceneContentUpdated(res)
      }
      setStatusText('正文创作完成！已填入中央阅读与编辑区。')
    } catch (err) {
      setStatusText(`创作失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleContinueWriting = async () => {
    if (!scene?.id) return alert('请先在左侧选择一个场景')
    setLoading(true)
    setStatusText('AI 正在顺承前文继续创作...')
    try {
      const res = await api.generateParagraph({
        scene_id: scene.id,
        tier: 'T3',
        instruction: instruction.trim() || '顺承前文继续创作下一段落',
      })
      if (res.generated_text) {
        setStreamingText(res.generated_text)
        setStatusText('续写完成，点击下方按钮可追加到正文。')
      }
    } catch (err) {
      setStatusText(`续写失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="inspector-tab-content">
      <div className="ai-cockpit-card">
        <span className="cockpit-title">AI 主创操作台</span>
        <div className="ai-actions-stack">
          <button className="btn-blue" onClick={handleAutoWriteScene} disabled={loading || !scene} style={{ height: '36px', fontSize: '13.5px' }}>
            {loading ? 'AI 正在创作中...' : 'AI 撰写当前场景正文'}
          </button>
          <div className="ai-actions-row">
            <button className="btn-small" style={{ flex: 1, height: '30px' }} onClick={handleContinueWriting} disabled={loading || !scene}>
              智能续写一段
            </button>
            <button className="btn-small" style={{ flex: 1, height: '30px' }} onClick={onAdvanceCompleted} disabled={loading}>
              自动连载下一章
            </button>
          </div>
        </div>
      </div>

      <div className="ai-cockpit-card">
        <span className="cockpit-title">给 AI 的剧情指导要求 (可选)</span>
        <textarea
          rows={4}
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="例如：反派在此处突然反目，语言要有压迫感，多描写心理活动与环境氛围..."
          style={{ width: '100%', resize: 'vertical', minHeight: '80px', boxSizing: 'border-box' }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn-small btn-blue" onClick={handleAutoWriteScene} disabled={loading || !scene}>
            按要求由 AI 创作
          </button>
        </div>
      </div>

      {thoughtProcess && <AgentThoughtStream thoughtProcess={thoughtProcess} />}

      {(statusText || streamingText) && (
        <div className="copilot-stream-box">
          <div className="stream-header">
            <span className="stream-status">{statusText}</span>
            {streamingText && (
              <button className="btn-small btn-blue" onClick={() => onApplyStreaming(streamingText)}>
                追加到正文
              </button>
            )}
          </div>
          {streamingText && <div className="stream-body">{streamingText}</div>}
        </div>
      )}
    </div>
  )
}
