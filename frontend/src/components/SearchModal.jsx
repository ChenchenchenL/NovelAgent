import React, { useState } from 'react'
import { FtsSearchPanel } from '../features/search/FtsSearchPanel'
import { VectorSearchPanel } from '../features/search/VectorSearchPanel'
import { KgBrowserPanel } from '../features/search/KgBrowserPanel'
import { HragAndContextPackPanel } from '../features/search/HragAndContextPackPanel'
import { IndexManagerPanel } from '../features/search/IndexManagerPanel'

export function SearchModal({ onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('fts')

  return (
    <div className="modal-overlay">
      <div className="modal-content search-modal" style={{ width: '920px', maxWidth: '94vw', height: '82vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>检索系统与上下文装配 (Search, KG, Vector & H-RAG)</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'fts' ? 'active' : ''}`} onClick={() => setActiveTab('fts')}>FTS全文检索</button>
          <button className={`tab-btn ${activeTab === 'vector' ? 'active' : ''}`} onClick={() => setActiveTab('vector')}>语义向量</button>
          <button className={`tab-btn ${activeTab === 'kg' ? 'active' : ''}`} onClick={() => setActiveTab('kg')}>知识图谱</button>
          <button className={`tab-btn ${activeTab === 'hrag' ? 'active' : ''}`} onClick={() => setActiveTab('hrag')}>ContextPack装配</button>
          <button className={`tab-btn ${activeTab === 'indexes' ? 'active' : ''}`} onClick={() => setActiveTab('indexes')}>索引管理</button>
        </div>
        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'fts' && <FtsSearchPanel />}
          {activeTab === 'vector' && <VectorSearchPanel />}
          {activeTab === 'kg' && <KgBrowserPanel />}
          {activeTab === 'hrag' && <HragAndContextPackPanel currentSceneId={currentSceneId} />}
          {activeTab === 'indexes' && <IndexManagerPanel />}
        </div>
      </div>
    </div>
  )
}
