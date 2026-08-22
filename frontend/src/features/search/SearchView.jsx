import React, { useState } from 'react'
import { FtsSearchPanel } from './FtsSearchPanel'
import { VectorSearchPanel } from './VectorSearchPanel'
import { KgBrowserPanel } from './KgBrowserPanel'
import { HragAndContextPackPanel } from './HragAndContextPackPanel'
import { IndexManagerPanel } from './IndexManagerPanel'

export function SearchView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('fts')

  const tabs = [
    { id: 'fts', label: 'FTS 全文检索' },
    { id: 'vector', label: '语义向量召回' },
    { id: 'kg', label: 'KG 知识图谱' },
    { id: 'hrag', label: 'H-RAG / ContextPack' },
    { id: 'indexes', label: '索引自愈管理' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>检索系统与上下文装配 (Search & RAG)</h2>
          <p className="view-subtitle">专名原句精确检索、语义向量召回、多跳图路径分析及写作 7 层 ContextPack 上下文打包。</p>
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
        {activeTab === 'fts' && <FtsSearchPanel />}
        {activeTab === 'vector' && <VectorSearchPanel />}
        {activeTab === 'kg' && <KgBrowserPanel />}
        {activeTab === 'hrag' && <HragAndContextPackPanel currentSceneId={currentSceneId} />}
        {activeTab === 'indexes' && <IndexManagerPanel />}
      </div>
    </div>
  )
}
