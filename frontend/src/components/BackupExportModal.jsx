import React, { useState } from 'react'
import { api } from '../api/client'

export function BackupExportModal({ onClose }) {
  const [msg, setMsg] = useState('')
  const [exportData, setExportData] = useState(null)
  const [restorePath, setRestorePath] = useState('')
  const [loading, setLoading] = useState(false)

  const handleBackup = async () => {
    setLoading(true)
    try {
      const res = await api.backupProject()
      setMsg(`备份创建成功！路径：${res.output_path}`)
    } catch (e) {
      setMsg(`备份失败: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    setLoading(true)
    try {
      const res = await api.exportProject({ format })
      setExportData(res)
      setMsg(`导出成功 (${format.toUpperCase()})`)
    } catch (e) {
      setMsg(`导出失败: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRestore = async (e) => {
    e.preventDefault()
    if (!restorePath) return
    setLoading(true)
    try {
      const res = await api.restoreProject({ backup_file: restorePath })
      setMsg(`还原成功！FSCK状态: ${res.fsck_status}, 已自动修复: ${res.auto_fixed}`)
    } catch (e) {
      setMsg(`还原失败: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content backup-modal">
        <div className="modal-header">
          <h3>💾 项目备份、导出与还原</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>
        {msg && <div className="notice-bar">{msg}</div>}
        <div className="backup-section">
          <h4>1. 完整备份</h4>
          <p>压缩打包当前数据库、正文版本与工作区配置为 .tar.gz 归档文件。</p>
          <button className="btn-primary" disabled={loading} onClick={handleBackup}>📦 立即创建项目备份</button>
        </div>
        <div className="backup-section">
          <h4>2. 全书导出</h4>
          <div className="btn-group">
            <button className="btn-secondary" disabled={loading} onClick={() => handleExport('markdown')}>📄 导出为 Markdown</button>
            <button className="btn-secondary" disabled={loading} onClick={() => handleExport('json')}>📑 导出为 JSON</button>
          </div>
          {exportData?.content && (
            <textarea className="export-preview" rows={6} readOnly value={exportData.content} />
          )}
        </div>
        <div className="backup-section">
          <h4>3. 从备份还原</h4>
          <form onSubmit={handleRestore} className="restore-form">
            <input type="text" placeholder="/path/to/backup.tar.gz" value={restorePath} onChange={(e) => setRestorePath(e.target.value)} required />
            <button type="submit" className="btn-danger" disabled={loading}>⚠️ 还原项目数据</button>
          </form>
        </div>
      </div>
    </div>
  )
}
