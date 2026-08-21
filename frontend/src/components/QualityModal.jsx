import React, { useState } from 'react'
import { BeatContractManager } from '../features/quality/BeatContractManager'
import { ClicheBlacklistManager } from '../features/quality/ClicheBlacklistManager'
import { VoiceFingerprintPanel } from '../features/quality/VoiceFingerprintPanel'
import { QualityInspectorPanel } from '../features/quality/QualityInspectorPanel'
import { FeedbackStatsPanel } from '../features/quality/FeedbackStatsPanel'

export function QualityModal({ isOpen, onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('quality')

  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content continuity-modal" style={{ width: '880px', maxWidth: '95vw', height: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>🛡️ 质量控制、Beat 契约与声音指纹</h3>
          <button className="btn-small" onClick={onClose}>✕</button>
        </div>

        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'quality' ? 'active' : ''}`} onClick={() => setActiveTab('quality')}>
            🔍 质量审查
          </button>
          <button className={`tab-btn ${activeTab === 'beat' ? 'active' : ''}`} onClick={() => setActiveTab('beat')}>
            ⏱️ Beat 契约
          </button>
          <button className={`tab-btn ${activeTab === 'cliche' ? 'active' : ''}`} onClick={() => setActiveTab('cliche')}>
            🚫 套话黑名单
          </button>
          <button className={`tab-btn ${activeTab === 'voice' ? 'active' : ''}`} onClick={() => setActiveTab('voice')}>
            🎭 声音指纹
          </button>
          <button className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`} onClick={() => setActiveTab('feedback')}>
            📊 反馈与去噪
          </button>
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
