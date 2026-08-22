import React, { useState } from 'react'
import { GraphRAGQueryPanel } from '../features/global/GraphRAGQueryPanel'
import { CommunityManager } from '../features/global/CommunityManager'
import { GlobalAuditPanel } from '../features/global/GlobalAuditPanel'
import { ModelStatsDashboard } from '../features/global/ModelStatsDashboard'
import { FeedbackOptimizerPanel } from '../features/global/FeedbackOptimizerPanel'

export function GlobalIntelligenceModal({ onClose }) {
  const [activeTab, setActiveTab] = useState('graphrag')

  return (
    <div className="modal-overlay">
      <div className="modal-content global-modal" style={{ width: '960px', maxWidth: '95vw', height: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>全局智能与全书分析 (GraphRAG, Communities & Audits)</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'graphrag' ? 'active' : ''}`} onClick={() => setActiveTab('graphrag')}>GraphRAG多跳查询</button>
          <button className={`tab-btn ${activeTab === 'communities' ? 'active' : ''}`} onClick={() => setActiveTab('communities')}>逻辑社区与摘要</button>
          <button className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>全书断裂审计</button>
          <button className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>Token与成本治理</button>
          <button className={`tab-btn ${activeTab === 'feedback_opt' ? 'active' : ''}`} onClick={() => setActiveTab('feedback_opt')}>反馈规则调优</button>
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
