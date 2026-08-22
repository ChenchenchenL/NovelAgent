import React, { useState } from 'react'
import { QualityInspectorPanel } from './QualityInspectorPanel'
import { BeatContractManager } from './BeatContractManager'
import { ClicheBlacklistManager } from './ClicheBlacklistManager'
import { VoiceFingerprintPanel } from './VoiceFingerprintPanel'
import { FeedbackStatsPanel } from './FeedbackStatsPanel'

export function QualityView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('quality')

  const tabs = [
    { id: 'quality', label: '质量与套话审查' },
    { id: 'beat', label: '节拍契约管理' },
    { id: 'cliche', label: '套话与口癖黑名单' },
    { id: 'voice', label: '人物声音指纹' },
    { id: 'feedback', label: '反馈与去噪审计' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>文本质控与声音指纹 (Quality & Voice)</h2>
          <p className="view-subtitle">防范语义重复与同义循环、套话扫描与过滤、主要人物语气指纹漂移审计及反馈去噪。</p>
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
        {activeTab === 'quality' && <QualityInspectorPanel currentSceneId={currentSceneId} />}
        {activeTab === 'beat' && <BeatContractManager currentSceneId={currentSceneId} />}
        {activeTab === 'cliche' && <ClicheBlacklistManager />}
        {activeTab === 'voice' && <VoiceFingerprintPanel />}
        {activeTab === 'feedback' && <FeedbackStatsPanel />}
      </div>
    </div>
  )
}
