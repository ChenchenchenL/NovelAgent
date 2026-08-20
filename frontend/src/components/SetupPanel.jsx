import React from 'react'

export function SetupPanel({
  currentPath,
  setCurrentPath,
  historyPaths,
  setHistoryPaths,
  onChooseDirectory,
  onOpenProject,
  disabled,
}) {
  return (
    <section className="setup panel">
      <div>
        <label>
          当前创作目录
          <input
            value={currentPath}
            onChange={e => setCurrentPath(e.target.value)}
            placeholder="选择或输入本地目录"
          />
        </label>
        <label>
          历史目录（只读）
          <textarea
            value={historyPaths}
            onChange={e => setHistoryPaths(e.target.value)}
          />
        </label>
      </div>
      <div className="actions">
        <button onClick={onChooseDirectory}>选择目录</button>
        <button onClick={onOpenProject} disabled={disabled}>
          打开项目
        </button>
      </div>
    </section>
  )
}
