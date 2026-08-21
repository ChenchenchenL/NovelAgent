import React from 'react'

export function GenerationProgress({ generating, statusText, streamingText, onCancel }) {
  if (!generating && !streamingText) return null

  return (
    <div className="generation-progress-box">
      <div className="generation-progress-header">
        <div className="generation-status-indicator">
          {generating && <span className="spinner-dot" />}
          <span>{statusText || (generating ? 'AI 正在生成中...' : '生成结束')}</span>
        </div>
        {generating && (
          <button className="btn-small btn-cancel" onClick={onCancel}>
            取消生成
          </button>
        )}
      </div>
      {streamingText && (
        <div className="generation-streaming-preview">
          <div className="preview-label">实时生成预览：</div>
          <div className="preview-content">{streamingText}</div>
        </div>
      )}
    </div>
  )
}
