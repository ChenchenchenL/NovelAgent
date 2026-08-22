import React, { useState } from 'react'
import { api } from '../../api/client'

export function DirectorHub({
  currentSceneId,
  onOpenAutoPlan,
  onSceneContentUpdated,
  onAdvanceCompleted,
}) {
  const [instruction, setInstruction] = useState('')
  const [messages, setMessages] = useState([
    { sender: 'ai', text: '小说主创工作台准备就绪。您可以输入大纲构思、场景推进或设定问答指令。' }
  ])
  const [loading, setLoading] = useState(false)

  const handleSend = async (e) => {
    e.preventDefault()
    if (!instruction.trim() || loading) return
    const userText = instruction.trim()
    setMessages((prev) => [...prev, { sender: 'user', text: userText }])
    setInstruction('')
    setLoading(true)

    try {
      const res = await api.directorChat({
        instruction: userText,
        current_scene_id: currentSceneId,
      })
      setMessages((prev) => [...prev, { sender: 'ai', text: res.reply }])
    } catch (err) {
      setMessages((prev) => [...prev, { sender: 'ai', text: `指令处理失败: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleAutoWriteScene = async () => {
    if (!currentSceneId) {
      alert('请先在左侧选择一个待创作的场景')
      return
    }
    setLoading(true)
    try {
      const res = await api.autoWriteScene({
        scene_id: currentSceneId,
        auto_extract: true,
      })
      if (onSceneContentUpdated) onSceneContentUpdated(res)
    } catch (err) {
      alert(`场景创作失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleAutoAdvance = async () => {
    setLoading(true)
    try {
      const res = await api.autoAdvanceScene()
      if (onAdvanceCompleted) onAdvanceCompleted(res)
    } catch (err) {
      alert(`自动连载推进失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="director-hub panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', borderLeft: '1px solid #282f3a', padding: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4>创作主控台</h4>
        <button className="btn-small btn-primary" onClick={onOpenAutoPlan}>全书大纲推演</button>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
        <button className="btn-small btn-primary" onClick={handleAutoWriteScene} disabled={loading || !currentSceneId} style={{ flex: 1 }}>
          推演当前场景
        </button>
        <button className="btn-small btn-primary" onClick={handleAutoAdvance} disabled={loading} style={{ flex: 1 }}>
          连载下一场景
        </button>
      </div>

      <div className="chat-stream" style={{ flex: 1, overflowY: 'auto', background: '#0e1115', padding: '8px', borderRadius: '6px', marginBottom: '10px' }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{ margin: '8px 0', textAlign: m.sender === 'user' ? 'right' : 'left' }}>
            <div style={{
              display: 'inline-block',
              maxWidth: '88%',
              padding: '6px 10px',
              borderRadius: '6px',
              background: m.sender === 'user' ? '#1e3a5f' : '#1c2128',
              color: '#f1f3f7',
              fontSize: '13px',
              textAlign: 'left',
              whiteSpace: 'pre-wrap',
            }}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend} style={{ display: 'flex', gap: '6px' }}>
        <input
          type="text"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="输入指导指令 (如: 加强悬疑感 / 查身世设定)..."
          style={{ flex: 1 }}
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading || !instruction.trim()}>
          发送
        </button>
      </form>
    </div>
  )
}
