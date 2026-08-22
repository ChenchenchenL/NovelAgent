import React, { useState } from 'react'
import { api } from '../../../api/client'

export function AiBrainstormTab({ scene, onApplyGuidance }) {
  const [ideas, setIdeas] = useState([])
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState('')

  const handleBrainstorm = async () => {
    if (!scene?.id) return alert('请先在左侧选择一个场景')
    setLoading(true)
    try {
      const res = await api.directorChat({
        instruction: question.trim() ? `请针对问题【${question.trim()}】构思 3 种出人意料但符合逻辑的情节发展` : '接下来可以怎么发展？请构思 3 种不同走向的戏剧冲突。',
        current_scene_id: scene.id,
      })
      setIdeas([res.reply])
    } catch (err) {
      alert(`构思失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="inspector-tab-content">
      <div className="ai-cockpit-card">
        <span className="cockpit-title">AI 情节与反转构思</span>
        <input
          placeholder="输入构思方向 (例如: 如何制造身份悬念?)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button className="btn-small btn-blue" onClick={handleBrainstorm} disabled={loading || !scene}>
          {loading ? 'AI 正在推演情节走向...' : '构思 3 种情节走向'}
        </button>
      </div>

      <div className="beats-list">
        {ideas.length === 0 ? (
          <div className="empty-hint">点击上方按钮，让 AI 结合当前大纲推演接下来的戏剧冲突与反转</div>
        ) : (
          ideas.map((item, idx) => (
            <div key={idx} className="beat-card" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.7' }}>
              <p style={{ fontSize: '13px', color: '#27272a' }}>{item}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
