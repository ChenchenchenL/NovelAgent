import React, { useState } from 'react'
import { PlotThreadManager } from '../plot/PlotThreadManager'
import { ForeshadowingManager } from '../plot/ForeshadowingManager'
import { TransitionInspector } from '../plot/TransitionInspector'
import { ImpactGraphViewer } from '../plot/ImpactGraphViewer'

export function PlanView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('threads')

  const tabs = [
    { id: 'threads', label: '主支剧情线与事件' },
    { id: 'foreshadowings', label: '伏笔生命周期与调度' },
    { id: 'transitions', label: '场景过渡连续性' },
    { id: 'impact', label: '影响图与失效传播' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>大纲与剧情规划 (Plan & Plot)</h2>
          <p className="view-subtitle">管理叙事主支线推进、伏笔预设与回收窗口、场景过渡连续性及修改影响图传播。</p>
        </div>
        <div className="view-tabs-bar">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`view-tab-btn ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="view-content-card">
        {activeTab === 'threads' && <PlotThreadManager currentSceneId={currentSceneId} />}
        {activeTab === 'foreshadowings' && <ForeshadowingManager currentSceneId={currentSceneId} />}
        {activeTab === 'transitions' && <TransitionInspector currentSceneId={currentSceneId} />}
        {activeTab === 'impact' && <ImpactGraphViewer currentSceneId={currentSceneId} />}
      </div>
    </div>
  )
}
