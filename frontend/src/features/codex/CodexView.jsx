import React, { useState } from 'react'
import { CharacterManager } from '../continuity/CharacterManager'
import { RelationshipManager } from '../continuity/RelationshipManager'
import { SecretManager } from '../continuity/SecretManager'
import { ItemConservationManager } from '../continuity/ItemConservationManager'
import { LocationMovementManager } from '../continuity/LocationMovementManager'

export function CodexView({ currentSceneId }) {
  const [activeTab, setActiveTab] = useState('characters')

  const tabs = [
    { id: 'characters', label: '人物档案' },
    { id: 'relationships', label: '人物关系' },
    { id: 'items', label: '关键道具' },
    { id: 'locations', label: '地点与时空' },
    { id: 'secrets', label: '叙事秘密' },
  ]

  return (
    <div className="continuity-subpanel">
      <div className="subpanel-nav-pills">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`subpanel-pill-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'characters' && <CharacterManager />}
        {activeTab === 'relationships' && <RelationshipManager currentSceneId={currentSceneId} />}
        {activeTab === 'items' && <ItemConservationManager currentSceneId={currentSceneId} />}
        {activeTab === 'locations' && <LocationMovementManager />}
        {activeTab === 'secrets' && <SecretManager currentSceneId={currentSceneId} />}
      </div>
    </div>
  )
}
