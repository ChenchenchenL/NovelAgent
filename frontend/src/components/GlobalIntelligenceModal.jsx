import React, { useState } from 'react'
import { CommunityManager } from '../features/global/CommunityManager'
import { GraphRAGQueryPanel } from '../features/global/GraphRAGQueryPanel'
import { GlobalAuditPanel } from '../features/global/GlobalAuditPanel'
import { ModelStatsDashboard } from '../features/global/ModelStatsDashboard'
import { FeedbackOptimizerPanel } from '../features/global/FeedbackOptimizerPanel'

export function GlobalIntelligenceModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('graphrag')

  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content continuity-modal" style={{ width: '920px', maxWidth: '95vw', height: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>🌐 GraphRAG、逻辑社区与全书智能回顾</h3>
          <button className="btn-small" onClick={onClose}>✕</button>
        </div>

        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'graphrag' ? 'active' : ''}`} onClick={() => setActiveTab('graphrag')}>
            🔍 GraphRAG 查询
          </button>
          <button className={`tab-btn ${activeTab === 'communities' ? 'active' : ''}`} onClick={() => setActiveTab('communities')}>
            🏘️ 逻辑社区与摘要
          </button>
          <button className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>
            📊 全书深度回顾
          </button>
          <button className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>
            📈 模型统计与成本
          </button>
          <button className={`tab-btn ${activeTab === 'feedback_opt' ? 'active' : ''}`} onClick={() => setActiveTab('feedback_opt')}>
            🎯 反馈优化与去噪
          </button>
        </div>

        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'graphrag' && <GraphRAGQueryPanel />}
          {activeTab === 'communities' && <CommunityManager />}
          {activeTab === 'audit' && <GlobalAuditPanel />}
          {activeTab === 'stats' && <ModelStatsDashboard />}
          {activeTab === 'feedback_opt' && <FeedbackOptimizerPanel />}
        </div>
      </div>
    </div>
  )
}
