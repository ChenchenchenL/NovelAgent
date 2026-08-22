import React, { useState } from 'react'
import { AiCopilotTab } from './tabs/AiCopilotTab'
import { SceneBeatsTab } from './tabs/SceneBeatsTab'
import { ContextTab } from './tabs/ContextTab'
import { ChapterTab } from './tabs/ChapterTab'

export function InspectorPanel({
  scene,
  selectedChapter,
  generating,
  statusText,
  streamingText,
  runs,
  onStartGeneration,
  onCancelGeneration,
  onApplyStreaming,
  onChangeChapterStatus,
}) {
  const [activeTab, setActiveTab] = useState('copilot')

  return (
    <aside className="inspector-panel">
      <div className="inspector-tabs-header">
        <button
          className={`inspector-tab-btn ${activeTab === 'copilot' ? 'active' : ''}`}
          onClick={() => setActiveTab('copilot')}
        >
          辅助推演
        </button>
        <button
          className={`inspector-tab-btn ${activeTab === 'beats' ? 'active' : ''}`}
          onClick={() => setActiveTab('beats')}
        >
          节拍契约
        </button>
        <button
          className={`inspector-tab-btn ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          连续性
        </button>
        <button
          className={`inspector-tab-btn ${activeTab === 'chapter' ? 'active' : ''}`}
          onClick={() => setActiveTab('chapter')}
        >
          章节流转
        </button>
      </div>

      <div className="inspector-body">
        {activeTab === 'copilot' && (
          <AiCopilotTab
            generating={generating}
            statusText={statusText}
            streamingText={streamingText}
            runs={runs}
            onStartGeneration={onStartGeneration}
            onCancelGeneration={onCancelGeneration}
            onApplyStreaming={onApplyStreaming}
          />
        )}
        {activeTab === 'beats' && <SceneBeatsTab scene={scene} />}
        {activeTab === 'context' && <ContextTab scene={scene} />}
        {activeTab === 'chapter' && (
          <ChapterTab
            selectedChapter={selectedChapter}
            onChangeChapterStatus={onChangeChapterStatus}
          />
        )}
      </div>
    </aside>
  )
}
