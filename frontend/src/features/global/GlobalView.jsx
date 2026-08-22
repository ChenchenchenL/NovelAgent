import React, { useState } from 'react'
import { GraphRAGQueryPanel } from './GraphRAGQueryPanel'
import { CommunityManager } from './CommunityManager'
import { GlobalAuditPanel } from './GlobalAuditPanel'
import { ModelStatsDashboard } from './ModelStatsDashboard'
import { FeedbackOptimizerPanel } from './FeedbackOptimizerPanel'

export function GlobalView() {
  const [activeTab, setActiveTab] = useState('graphrag')

  const tabs = [
    { id: 'graphrag', label: 'GraphRAG 多跳查询' },
    { id: 'communities', label: '逻辑社区与层级摘要' },
    { id: 'audit', label: '全书回顾与断裂审计' },
    { id: 'stats', label: '模型调用与 Token 成本' },
    { id: 'feedback_opt', label: '反馈驱动规则优化' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>全局智能与 GraphRAG (Global Intelligence)</h2>
          <p className="view-subtitle">跨卷多跳主题分析、社区自动聚类与摘要增量失效、全书人物弧回顾及模型 Token 成本治理。</p>
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
        {activeTab === 'graphrag' && <GraphRAGQueryPanel />}
        {activeTab === 'communities' && <CommunityManager />}
        {activeTab === 'audit' && <GlobalAuditPanel />}
        {activeTab === 'stats' && <ModelStatsDashboard />}
        {activeTab === 'feedback_opt' && <FeedbackOptimizerPanel />}
      </div>
    </div>
  )
}
