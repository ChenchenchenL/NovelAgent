import React, { useState } from 'react'
import { api } from '../../api/client'
import { AgentThoughtStream } from '../agent/AgentThoughtStream'

export function WritingDirector({
  scene,
  onSceneContentUpdated,
  onAdvanceCompleted,
  onOpenNewStory,
}) {
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastThought, setLastThought] = useState(null)
  const [reply, setReply] = useState('')

  const runAction = async (action) => {
    setLoading(true)
    setReply('')
    try {
      if (action === 'write') {
        if (!scene?.id) return alert('请先在左侧选择一个场景')
        const res = await api.autoWriteScene({ scene_id: scene.id, auto_extract: true, guidance: instruction || undefined })
        setLastThought(res.thought_process)
        if (onSceneContentUpdated) onSceneContentUpdated(res)
        setReply('场景已推演完毕，正文已填入编辑区。')
      } else if (action === 'advance') {
        const res = await api.autoAdvanceScene()
        setLastThought(res.thought_process)
        if (onAdvanceCompleted) onAdvanceCompleted(res)
        setReply('已自动推进并推演下一个场景。')
      } else if (action === 'chat') {
        if (!instruction.trim()) return
        const res = await api.directorChat({ instruction: instruction.trim(), current_scene_id: scene?.id })
        setReply(res.reply)
        setLastThought(null)
      }
    } catch (err) {
      setReply(`出错了：${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runAction('chat') }
  }

  return (
    <aside className="inspector-panel" style={{ display: 'flex', flexDirection: 'column', padding: '16px', gap: '12px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button className="btn-primary" onClick={() => runAction('write')} disabled={loading || !scene}>
          {loading ? '推演中…' : '推演此场景正文'}
        </button>
        <button
          onClick={() => runAction('advance')}
          disabled={loading}
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #282f3a', background: '#1c2128', color: '#cbd5e1', cursor: 'pointer', textAlign: 'left' }}
        >
          自动连载下一场景
        </button>
        <button
          onClick={onOpenNewStory}
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #282f3a', background: '#1c2128', color: '#94a3b8', cursor: 'pointer', textAlign: 'left' }}
        >
          全书大纲与设定规划
        </button>
      </div>

      {lastThought && <AgentThoughtStream thoughtProcess={lastThought} />}

      {reply && (
        <div style={{ padding: '10px', background: '#161a21', borderRadius: '4px', fontSize: '13px', color: '#cbd5e1', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
          {reply}
        </div>
      )}

      <div style={{ marginTop: 'auto' }}>
        <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>指导与修改指令：</p>
        <textarea
          rows={3}
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={handleKey}
          placeholder="例如：让这段对话更紧张一些，突出心理博弈..."
          disabled={loading}
          style={{ width: '100%', marginBottom: '8px', resize: 'vertical' }}
        />
        <button
          className="btn-primary"
          style={{ width: '100%' }}
          onClick={() => runAction('chat')}
          disabled={loading || !instruction.trim()}
        >
          发送指令
        </button>
      </div>
    </aside>
  )
}
