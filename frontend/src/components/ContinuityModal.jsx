import React, { useState } from 'react'
import { CharacterManager } from '../features/continuity/CharacterManager'
import { RelationshipManager } from '../features/continuity/RelationshipManager'
import { SecretManager } from '../features/continuity/SecretManager'
import { ItemConservationManager } from '../features/continuity/ItemConservationManager'
import { ShadowRevealManager } from '../features/continuity/ShadowRevealManager'
import { LocationMovementManager } from '../features/continuity/LocationMovementManager'

export function ContinuityModal({ isOpen, onClose, currentSceneId }) {
  const [tab, setTab] = useState('characters')

  if (!isOpen) return null

  return (
    <div className="modal-backdrop">
      <div className="modal-content continuity-modal" style={{ maxWidth: 800 }}>
        <div className="modal-header">
          <h3>连续性与世界观设定 (Continuity Workbench)</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <div className="tab-nav">
          <button className={`tab-btn ${tab === 'characters' ? 'active' : ''}`} onClick={() => setTab('characters')}>👤 人物档案</button>
          <button className={`tab-btn ${tab === 'relationships' ? 'active' : ''}`} onClick={() => setTab('relationships')}>🔗 人物关系</button>
          <button className={`tab-btn ${tab === 'secrets' ? 'active' : ''}`} onClick={() => setTab('secrets')}>🔒 叙事秘密</button>
          <button className={`tab-btn ${tab === 'items' ? 'active' : ''}`} onClick={() => setTab('items')}>🗡️ 物品守恒</button>
          <button className={`tab-btn ${tab === 'shadows' ? 'active' : ''}`} onClick={() => setTab('shadows')}>🎭 影子与掉马</button>
          <button className={`tab-btn ${tab === 'locations' ? 'active' : ''}`} onClick={() => setTab('locations')}>📍 地点与时空</button>
        </div>
        <div className="modal-body" style={{ minHeight: 380, maxHeight: 520, overflowY: 'auto' }}>
          {tab === 'characters' && <CharacterManager />}
          {tab === 'relationships' && <RelationshipManager currentSceneId={currentSceneId} />}
          {tab === 'secrets' && <SecretManager currentSceneId={currentSceneId} />}
          {tab === 'items' && <ItemConservationManager currentSceneId={currentSceneId} />}
          {tab === 'shadows' && <ShadowRevealManager currentSceneId={currentSceneId} />}
          {tab === 'locations' && <LocationMovementManager />}
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
