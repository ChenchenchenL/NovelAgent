import React, { useState } from 'react'
import { CharacterManager } from '../continuity/CharacterManager'
import { RelationshipManager } from '../continuity/RelationshipManager'
import { SecretManager } from '../continuity/SecretManager'
import { ItemConservationManager } from '../continuity/ItemConservationManager'
import { ShadowRevealManager } from '../continuity/ShadowRevealManager'
import { LocationMovementManager } from '../continuity/LocationMovementManager'

export function CodexView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('characters')

  const tabs = [
    { id: 'characters', label: '人物档案' },
    { id: 'relationships', label: '关系演进' },
    { id: 'secrets', label: '叙事秘密' },
    { id: 'items', label: '物品守恒' },
    { id: 'shadows', label: '影子与掉马' },
    { id: 'locations', label: '地点与时空' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>世界观与设定正典 (Codex & Story Bible)</h2>
          <p className="view-subtitle">设定权威事实基准：人物核心档案、不对称关系演进、秘密知情账本、关键道具所有权守恒与地理时空移动规则。</p>
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
        {activeTab === 'characters' && <CharacterManager />}
        {activeTab === 'relationships' && <RelationshipManager currentSceneId={currentSceneId} />}
        {activeTab === 'secrets' && <SecretManager currentSceneId={currentSceneId} />}
        {activeTab === 'items' && <ItemConservationManager currentSceneId={currentSceneId} />}
        {activeTab === 'shadows' && <ShadowRevealManager currentSceneId={currentSceneId} />}
        {activeTab === 'locations' && <LocationMovementManager />}
      </div>
    </div>
  )
}
