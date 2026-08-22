import React, { useState } from 'react'
import { QualityInspectorPanel } from '../features/quality/QualityInspectorPanel'
import { BeatContractManager } from '../features/quality/BeatContractManager'
import { ClicheBlacklistManager } from '../features/quality/ClicheBlacklistManager'
import { VoiceFingerprintPanel } from '../features/quality/VoiceFingerprintPanel'
import { FeedbackStatsPanel } from '../features/quality/FeedbackStatsPanel'

export function QualityModal({ onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('quality')

  return (
    <div className="modal-overlay">
      <div className="modal-content quality-modal" style={{ width: '920px', maxWidth: '94vw', height: '82vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>文本质控、Beat 契约与声音指纹</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'quality' ? 'active' : ''}`} onClick={() => setActiveTab('quality')}>质量审查</button>
          <button className={`tab-btn ${activeTab === 'beat' ? 'active' : ''}`} onClick={() => setActiveTab('beat')}>节拍契约</button>
          <button className={`tab-btn ${activeTab === 'cliche' ? 'active' : ''}`} onClick={() => setActiveTab('cliche')}>套话黑名单</button>
          <button className={`tab-btn ${activeTab === 'voice' ? 'active' : ''}`} onClick={() => setActiveTab('voice')}>声音指纹</button>
          <button className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`} onClick={() => setActiveTab('feedback')}>作者反馈</button>
        </div>
        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'quality' && <QualityInspectorPanel currentSceneId={currentSceneId} />}
          {activeTab === 'beat' && <BeatContractManager currentSceneId={currentSceneId} />}
          {activeTab === 'cliche' && <ClicheBlacklistManager />}
          {activeTab === 'voice' && <VoiceFingerprintPanel />}
          {activeTab === 'feedback' && <FeedbackStatsPanel />}
        </div>
      </div>
    </div>
  )
}
