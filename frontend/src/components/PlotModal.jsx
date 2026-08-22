import React, { useState } from 'react'
import { PlotThreadManager } from '../features/plot/PlotThreadManager'
import { ForeshadowingManager } from '../features/plot/ForeshadowingManager'
import { TransitionInspector } from '../features/plot/TransitionInspector'
import { ImpactGraphViewer } from '../features/plot/ImpactGraphViewer'

export function PlotModal({ onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('threads')

  return (
    <div className="modal-overlay">
      <div className="modal-content plot-modal" style={{ width: '900px', maxWidth: '92vw', height: '80vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>大纲与剧情规划 (Plot Threads, Foreshadowing & Impact)</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'threads' ? 'active' : ''}`} onClick={() => setActiveTab('threads')}>剧情线事件</button>
          <button className={`tab-btn ${activeTab === 'foreshadowings' ? 'active' : ''}`} onClick={() => setActiveTab('foreshadowings')}>伏笔调度</button>
          <button className={`tab-btn ${activeTab === 'transitions' ? 'active' : ''}`} onClick={() => setActiveTab('transitions')}>场景过渡连续性</button>
          <button className={`tab-btn ${activeTab === 'impact' ? 'active' : ''}`} onClick={() => setActiveTab('impact')}>影响图传播</button>
        </div>
        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'threads' && <PlotThreadManager currentSceneId={currentSceneId} />}
          {activeTab === 'foreshadowings' && <ForeshadowingManager currentSceneId={currentSceneId} />}
          {activeTab === 'transitions' && <TransitionInspector currentSceneId={currentSceneId} />}
          {activeTab === 'impact' && <ImpactGraphViewer currentSceneId={currentSceneId} />}
        </div>
      </div>
    </div>
  )
}
