import React, { useState } from 'react'
import { PlanView } from './PlanView'
import { CodexView } from '../codex/CodexView'

export function OutlineModal({ isOpen, onClose, currentSceneId, onOpenAutoPlan }) {
  const [tab, setTab] = useState('plan')

  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: '920px', maxWidth: '95vw', height: '82vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <h3>故事大纲与全书设定</h3>
            <button className="btn-sm btn-blue" onClick={onOpenAutoPlan}>
              AI 重新规划全书
            </button>
          </div>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="inspector-tabs-header" style={{ padding: '0 12px' }}>
          <button
            className={`inspector-tab-btn ${tab === 'plan' ? 'active' : ''}`}
            onClick={() => setTab('plan')}
          >
            剧情线与大纲结构
          </button>
          <button
            className={`inspector-tab-btn ${tab === 'codex' ? 'active' : ''}`}
            onClick={() => setTab('codex')}
          >
            人物档案与世界设定
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
          {tab === 'plan' && <PlanView currentSceneId={currentSceneId} />}
          {tab === 'codex' && <CodexView currentSceneId={currentSceneId} />}
        </div>
      </div>
    </div>
  )
}
