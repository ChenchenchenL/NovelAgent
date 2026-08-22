import React, { useState } from 'react'
import { CodexView } from '../features/codex/CodexView'
import { PlanView } from '../features/plan/PlanView'
import { SearchView } from '../features/search/SearchView'
import { QualityView } from '../features/quality/QualityView'
import { GlobalView } from '../features/global/GlobalView'

export function WorldMemoryInspectorModal({ isOpen, onClose, currentSceneId }) {
  const [tab, setTab] = useState('codex')

  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content continuity-modal" style={{ width: '980px', maxWidth: '96vw', height: '88vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>世界观设定与全书记忆透视</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="continuity-tabs">
          <button className={`tab-btn ${tab === 'codex' ? 'active' : ''}`} onClick={() => setTab('codex')}>
            实体与连续性 (人物/道具/位置)
          </button>
          <button className={`tab-btn ${tab === 'plan' ? 'active' : ''}`} onClick={() => setTab('plan')}>
            剧情线与伏笔网络
          </button>
          <button className={`tab-btn ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>
            图谱与检索 (KG/FTS/向量)
          </button>
          <button className={`tab-btn ${tab === 'quality' ? 'active' : ''}`} onClick={() => setTab('quality')}>
            质控自省与音色
          </button>
          <button className={`tab-btn ${tab === 'global' ? 'active' : ''}`} onClick={() => setTab('global')}>
            GraphRAG 与全局分析
          </button>
        </div>

        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {tab === 'codex' && <CodexView currentSceneId={currentSceneId} />}
          {tab === 'plan' && <PlanView currentSceneId={currentSceneId} />}
          {tab === 'search' && <SearchView currentSceneId={currentSceneId} />}
          {tab === 'quality' && <QualityView currentSceneId={currentSceneId} />}
          {tab === 'global' && <GlobalView />}
        </div>
      </div>
    </div>
  )
}
