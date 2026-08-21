import React, { useState } from 'react'
import { api } from '../../api/client'

export function HragAndContextPackPanel({ currentSceneId }) {
  const [instruction, setInstruction] = useState('')
  const [contextPack, setContextPack] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAssemble = async () => {
    if (!currentSceneId) return
    setLoading(true)
    try {
      const res = await api.assembleContextPack({
        scene_id: currentSceneId,
        instruction: instruction.trim() || undefined,
        max_tokens: 6000,
      })
      setContextPack(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="continuity-subpanel">
      {!currentSceneId ? (
        <div className="empty-state">请先在左侧选择场景以装配 ContextPack</div>
      ) : (
        <div>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <input
              type="text"
              placeholder="作者提示指令 (选填)..."
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="btn-primary" onClick={handleAssemble} disabled={loading}>
              {loading ? '装配中...' : '📦 装配 7 层上下文包'}
            </button>
          </div>

          {contextPack && (
            <div>
              <div className="continuity-card" style={{ marginBottom: '12px' }}>
                <div className="continuity-card-header">
                  <strong>装配完成: 共 {contextPack.fragments.length} 个片段</strong>
                  <span className="badge success">Token 估算: {contextPack.total_tokens}</span>
                </div>
              </div>
              <div className="continuity-list">
                {contextPack.fragments.map((f, idx) => (
                  <div key={idx} className="continuity-card">
                    <div className="continuity-card-header">
                      <span>
                        <span className="badge gray">{f.fragment_type}</span>{' '}
                        <strong>来源 #{f.source_id} (v{f.source_version})</strong>
                      </span>
                      <span className="badge success">
                        {f.truncatable ? '可截断' : '保留'} | {f.tokens} tokens
                      </span>
                    </div>
                    <p style={{ marginTop: '6px', fontSize: '13px', whiteSpace: 'pre-wrap' }}>
                      {f.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
