import React, { useState } from 'react'
import { api } from '../../../api/client'
import { AgentThoughtStream } from '../../agent/AgentThoughtStream'

export function AiWriterTab({
  scene,
  draftContent,
  onApplyStreaming,
  onSceneContentUpdated,
  onAdvanceCompleted,
}) {
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [thoughtProcess, setThoughtProcess] = useState(null)

  const handleWriteScene = async () => {
    if (!scene?.id) return alert('请先在左侧选择一个场景')
    setLoading(true)
    setStatusText('AI 正在结合前文与大纲推演正文...')
    setStreamingText('')
    try {
      const res = await api.autoWriteScene({ scene_id: scene.id, auto_extract: true, guidance: instruction || undefined })
      setThoughtProcess(res.thought_process)
      if (res.content) {
        setStreamingText(res.content)
        if (onSceneContentUpdated) onSceneContentUpdated(res)
      }
      setStatusText('场景初稿推演完成！已自动填入草稿区。')
    } catch (err) {
      setStatusText(`推演失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleContinueWriting = async () => {
    if (!scene?.id) return alert('请先在左侧选择一个场景')
    setLoading(true)
    setStatusText('AI 正在续写下一段落...')
    try {
      const res = await api.generateParagraph({
        scene_id: scene.id,
        tier: 'T3',
        instruction: instruction || '顺承前文继续创作下一段落',
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button className="btn-blue" onClick={handleWriteScene} disabled={loading || !scene}>
          {loading ? 'AI 推演中...' : 'AI 撰写当前场景正文'}
        </button>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button className="btn-small" style={{ flex: 1 }} onClick={handleContinueWriting} disabled={loading || !scene}>
            智能续写一段
          </button>
          <button className="btn-small" style={{ flex: 1 }} onClick={onAdvanceCompleted} disabled={loading}>
            连载下一场景
          </button>
        </div>
      </div>

      <div className="form-group-compact" style={{ marginTop: '6px' }}>
        <label>创作指令与细节要求 (可选)</label>
        <textarea
          rows={3}
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="例如：着重描写二人的心理对峙，语言节奏要快..."
        />
      </div>

      {thoughtProcess && <AgentThoughtStream thoughtProcess={thoughtProcess} />}

      {(statusText || streamingText) && (
        <div className="copilot-stream-box">
          <div className="stream-header">
            <span className="stream-status">{statusText}</span>
            {streamingText && (
              <button className="btn-apply-stream" onClick={() => onApplyStreaming(streamingText)}>
                追加到草稿
              </button>
            )}
          </div>
          {streamingText && <div className="stream-body">{streamingText}</div>}
        </div>
      )}
    </div>
  )
}
