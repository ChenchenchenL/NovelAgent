import React from 'react'

export function NoticeToast({ notice, onDismiss }) {
  if (!notice) return null

  const isError = notice.includes('失败') || notice.includes('错误') || notice.includes('阻断')
  const isWarning = notice.includes('警告') || notice.includes('冲突')

  const badgeClass = isError ? 'toast-error' : isWarning ? 'toast-warning' : 'toast-info'
  const tagLabel = isError ? '错误' : isWarning ? '提示' : '状态'

  return (
    <div className={`notice-toast ${badgeClass}`}>
      <span className="toast-tag">{tagLabel}</span>
      <span className="toast-message">{notice}</span>
      {onDismiss && (
        <button className="toast-close-btn" onClick={onDismiss} title="关闭">
          ✕
        </button>
      )}
    </div>
  )
}
