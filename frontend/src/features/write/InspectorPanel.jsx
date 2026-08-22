import React, { useState } from 'react'
import { AiWriteTab } from './tabs/AiWriteTab'
import { AiBrainstormTab } from './tabs/AiBrainstormTab'
import { CharacterQuickTab } from './tabs/CharacterQuickTab'

export function InspectorPanel({
  scene,
  onApplyStreaming,
  onSceneContentUpdated,
  onAdvanceCompleted,
}) {
  const [activeTab, setActiveTab] = useState('write')

  return (
    <aside className="inspector-panel">
      <div className="inspector-tabs-header">
        <button
          className={`inspector-tab-btn ${activeTab === 'write' ? 'active' : ''}`}
          onClick={() => setActiveTab('write')}
        >
          AI 创作
        </button>
        <button
          className={`inspector-tab-btn ${activeTab === 'brainstorm' ? 'active' : ''}`}
          onClick={() => setActiveTab('brainstorm')}
        >
          情节构思
        </button>
        <button
          className={`inspector-tab-btn ${activeTab === 'chars' ? 'active' : ''}`}
          onClick={() => setActiveTab('chars')}
        >
          登场人物
        </button>
      </div>

      <div className="inspector-body">
        {activeTab === 'write' && (
          <AiWriteTab
            scene={scene}
            onApplyStreaming={onApplyStreaming}
            onSceneContentUpdated={onSceneContentUpdated}
            onAdvanceCompleted={onAdvanceCompleted}
          />
        )}
        {activeTab === 'brainstorm' && <AiBrainstormTab scene={scene} />}
        {activeTab === 'chars' && <CharacterQuickTab />}
      </div>
    </aside>
  )
}
