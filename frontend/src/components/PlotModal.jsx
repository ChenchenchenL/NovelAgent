import React, { useState } from 'react'
import { PlotThreadManager } from '../features/plot/PlotThreadManager'
import { ForeshadowingManager } from '../features/plot/ForeshadowingManager'
import { TransitionInspector } from '../features/plot/TransitionInspector'
import { ImpactGraphViewer } from '../features/plot/ImpactGraphViewer'

export function PlotModal({ isOpen, onClose, currentSceneId }) {
  const [tab, setTab] = useState('threads')

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content continuity-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-tabs">
            <button className={`tab-btn ${tab === 'threads' ? 'active' : ''}`} onClick={() => setTab('threads')}>
              📈 剧情线 & 事件
            </button>
            <button className={`tab-btn ${tab === 'foreshadowings' ? 'active' : ''}`} onClick={() => setTab('foreshadowings')}>
              🪝 伏笔生命周期
            </button>
            <button className={`tab-btn ${tab === 'transitions' ? 'active' : ''}`} onClick={() => setTab('transitions')}>
              🔍 场景过渡检查
            </button>
            <button className={`tab-btn ${tab === 'impact' ? 'active' : ''}`} onClick={() => setTab('impact')}>
              🕸️ Impact Graph
            </button>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {tab === 'threads' && <PlotThreadManager currentSceneId={currentSceneId} />}
          {tab === 'foreshadowings' && <ForeshadowingManager currentSceneId={currentSceneId} />}
          {tab === 'transitions' && <TransitionInspector currentSceneId={currentSceneId} />}
          {tab === 'impact' && <ImpactGraphViewer currentSceneId={currentSceneId} />}
        </div>
      </div>
    </div>
  )
}
