import React, { useState } from 'react'
import { PlotThreadManager } from '../plot/PlotThreadManager'
import { ForeshadowingManager } from '../plot/ForeshadowingManager'
import { TransitionInspector } from '../plot/TransitionInspector'

export function PlanView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('threads')

  const tabs = [
    { id: 'threads', label: '剧情主支线与事件' },
    { id: 'foreshadowings', label: '伏笔预设与回收' },
    { id: 'transitions', label: '场景过渡与衔接' },
  ]

  return (
    <div className="continuity-subpanel">
      <div className="subpanel-nav-pills">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`subpanel-pill-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'threads' && <PlotThreadManager currentSceneId={currentSceneId} />}
        {activeTab === 'foreshadowings' && <ForeshadowingManager currentSceneId={currentSceneId} />}
        {activeTab === 'transitions' && <TransitionInspector currentSceneId={currentSceneId} />}
      </div>
    </div>
  )
}
