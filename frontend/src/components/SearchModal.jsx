import React, { useState } from 'react'
import { FtsSearchPanel } from '../features/search/FtsSearchPanel'
import { VectorSearchPanel } from '../features/search/VectorSearchPanel'
import { KgBrowserPanel } from '../features/search/KgBrowserPanel'
import { HragAndContextPackPanel } from '../features/search/HragAndContextPackPanel'
import { IndexManagerPanel } from '../features/search/IndexManagerPanel'

export function SearchModal({ isOpen, onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('fts')

  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content continuity-modal" style={{ width: '880px', maxWidth: '95vw', height: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>🔎 检索系统、KG 与 ContextPack</h3>
          <button className="btn-small" onClick={onClose}>✕</button>
        </div>

        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'fts' ? 'active' : ''}`} onClick={() => setActiveTab('fts')}>
            🔍 FTS 全文检索
          </button>
          <button className={`tab-btn ${activeTab === 'vector' ? 'active' : ''}`} onClick={() => setActiveTab('vector')}>
            🧬 向量相似度
          </button>
          <button className={`tab-btn ${activeTab === 'kg' ? 'active' : ''}`} onClick={() => setActiveTab('kg')}>
            🕸️ KG 知识图谱
          </button>
          <button className={`tab-btn ${activeTab === 'hrag' ? 'active' : ''}`} onClick={() => setActiveTab('hrag')}>
            📦 H-RAG / ContextPack
          </button>
          <button className={`tab-btn ${activeTab === 'indexes' ? 'active' : ''}`} onClick={() => setActiveTab('indexes')}>
            ⚙️ 索引重建
          </button>
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
