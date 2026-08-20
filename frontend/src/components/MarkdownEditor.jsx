import React, { useRef } from 'react'

export function MarkdownEditor({
  draftContent,
  isSaving,
  hasSnapshot,
  canUndo,
  canRedo,
  readOnly = false,
  banner = null,
  onContentChange,
  onUndo,
  onRedo,
  onSnapshot,
  onRestore,
  onReset,
}) {
  const textareaRef = useRef(null)

  const handleKeyDown = (e) => {
    if (readOnly) return
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault()
      if (e.shiftKey) {
        onRedo()
      } else {
        onUndo()
      }
    }
  }

  const handleChange = (e) => {
    if (readOnly) return
    const val = e.target.value
    const cursor = e.target.selectionStart || 0
    onContentChange(val, cursor)
  }

  return (
    <div className="markdown-editor-container">
      {banner}
      <div className="editor-toolbar">
        <div className="toolbar-group">
          <button disabled={readOnly || !canUndo} onClick={onUndo} title="撤销 (Ctrl+Z)">↶ 撤销</button>
          <button disabled={readOnly || !canRedo} onClick={onRedo} title="重做 (Ctrl+Shift+Z)">↷ 重做</button>
          <button disabled={readOnly} onClick={onSnapshot} title="保存快照到本地数据库">📷 快照</button>
          <button disabled={readOnly || !hasSnapshot} onClick={onRestore} title="从快照恢复草稿">↺ 恢复</button>
          <button disabled={readOnly} onClick={onReset} title="清空工作区并与正典同步">⟲ 重置</button>
        </div>
        <div className="toolbar-status">
          {readOnly ? (
            <span className="status-readonly">只读预览模式</span>
          ) : isSaving ? (
            <span className="status-saving">正在保存工作区...</span>
          ) : (
            <span className="status-saved">工作区已同步</span>
          )}
        </div>
      </div>
      <textarea
        ref={textareaRef}
        className="editor-textarea"
        value={draftContent}
        readOnly={readOnly}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={readOnly ? '只读预览历史版本...' : '在此编写正文草稿（支持 Markdown 语法与 Ctrl+Z 撤销/重做）...'}
      />
    </div>
  )
}
