import React from 'react'

export function ContractPanel({ scene }) {
  if (!scene) return null

  return (
    <div className="contracts-view">
      <h3>场景进入契约 (SceneEntryContract)</h3>
      <pre>{JSON.stringify(scene.entry_contract || { note: '暂无进入契约' }, null, 2)}</pre>
      <h3>场景退出状态 (SceneExitState)</h3>
      <pre>{JSON.stringify(scene.exit_state || { note: '暂无退出状态' }, null, 2)}</pre>
    </div>
  )
}
