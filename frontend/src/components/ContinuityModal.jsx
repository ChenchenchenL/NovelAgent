import React, { useState } from 'react'
import { CharacterManager } from '../features/continuity/CharacterManager'
import { RelationshipManager } from '../features/continuity/RelationshipManager'
import { SecretManager } from '../features/continuity/SecretManager'
import { ItemConservationManager } from '../features/continuity/ItemConservationManager'
import { ShadowRevealManager } from '../features/continuity/ShadowRevealManager'
import { LocationMovementManager } from '../features/continuity/LocationMovementManager'

export function ContinuityModal({ onClose, currentSceneId }) {
  const [activeTab, setActiveTab] = useState('characters')

  return (
    <div className="modal-overlay">
      <div className="modal-content continuity-modal" style={{ width: '880px', maxWidth: '90vw', height: '80vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h3>正典连续性与世界观实体管理</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="continuity-tabs">
          <button className={`tab-btn ${activeTab === 'characters' ? 'active' : ''}`} onClick={() => setActiveTab('characters')}>人物档案</button>
          <button className={`tab-btn ${activeTab === 'relationships' ? 'active' : ''}`} onClick={() => setActiveTab('relationships')}>关系演进</button>
          <button className={`tab-btn ${activeTab === 'secrets' ? 'active' : ''}`} onClick={() => setActiveTab('secrets')}>叙事秘密</button>
          <button className={`tab-btn ${activeTab === 'items' ? 'active' : ''}`} onClick={() => setActiveTab('items')}>物品守恒</button>
          <button className={`tab-btn ${activeTab === 'shadows' ? 'active' : ''}`} onClick={() => setActiveTab('shadows')}>影子掉马</button>
          <button className={`tab-btn ${activeTab === 'locations' ? 'active' : ''}`} onClick={() => setActiveTab('locations')}>地点时空</button>
        </div>
        <div className="continuity-body" style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'characters' && <CharacterManager />}
          {activeTab === 'relationships' && <RelationshipManager currentSceneId={currentSceneId} />}
          {activeTab === 'secrets' && <SecretManager currentSceneId={currentSceneId} />}
          {activeTab === 'items' && <ItemConservationManager currentSceneId={currentSceneId} />}
          {activeTab === 'shadows' && <ShadowRevealManager currentSceneId={currentSceneId} />}
          {activeTab === 'locations' && <LocationMovementManager />}
        </div>
      </div>
    </div>
  )
}
