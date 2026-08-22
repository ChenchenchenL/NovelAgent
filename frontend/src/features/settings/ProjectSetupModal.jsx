import React, { useState } from 'react'

export function ProjectSetupModal({
  isOpen,
  onClose,
  currentPath,
  setCurrentPath,
  historyPaths = [],
  onOpenProject,
}) {
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleOpen = async (path) => {
    const target = path || currentPath
    if (!target?.trim()) return
    setLoading(true)
    setNotice('')
    try {
      if (path) setCurrentPath(path)
      await onOpenProject(path)
      onClose()
    } catch (err) {
      setNotice(`打开项目失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: '560px', maxWidth: '92vw' }}>
        <div className="modal-header">
          <h3>小说项目存储目录</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ fontSize: '13px', color: '#52525b', lineHeight: '1.6' }}>
            选择本地文件夹作为小说的存储空间。NovelAgent 将在本地自动维护不可变正典、大纲与版本快照。
          </p>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={currentPath}
              onChange={(e) => setCurrentPath(e.target.value)}
              placeholder="例如: /home/user/my_novel"
              style={{ flex: 1 }}
            />
            <button className="btn-blue" onClick={() => handleOpen()} disabled={loading}>
              {loading ? '正在打开...' : '打开 / 初始化'}
            </button>
          </div>

          {notice && <div style={{ color: '#ef4444', fontSize: '12.5px' }}>{notice}</div>}

          {historyPaths.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <span style={{ fontSize: '12px', color: '#71717a', fontWeight: 600 }}>最近打开的项目：</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                {historyPaths.map((p, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleOpen(p)}
                    style={{ padding: '6px 10px', background: '#fafafa', border: '1px solid #e4e4e7', borderRadius: '4px', fontSize: '12.5px', cursor: 'pointer', color: '#2563eb' }}
                  >
                    {p}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
