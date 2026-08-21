import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export function FsckModal({ onClose }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const handleRunFsck = async (fix = false) => {
    setLoading(true)
    try {
      const res = fix ? await api.runFsckFix() : await api.runFsck()
      setReport(res)
      setMsg(fix ? `修复完成，已修复 ${res.auto_fixed} 处问题` : `检查完成，状态: ${res.status}`)
    } catch (e) {
      setMsg(`执行失败: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleRunFsck(false)
  }, [])

  const handleResolveConflict = async (journalId, resolution) => {
    try {
      await api.resolveFsckConflict({ journal_id: journalId, resolution })
      setMsg(`已应用决议: ${resolution}`)
      await handleRunFsck(false)
    } catch (e) {
      setMsg(`决议失败: ${e.message}`)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content fsck-modal">
        <div className="modal-header">
          <h3>🩺 跨介质一致性检查 (FSCK)</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>
        {msg && <div className="notice-bar">{msg}</div>}
        <div className="fsck-toolbar">
          <button className="btn-secondary" disabled={loading} onClick={() => handleRunFsck(false)}>重新检查</button>
          <button className="btn-primary" disabled={loading} onClick={() => handleRunFsck(true)}>🛠️ 一键自动修复缺失文件与索引</button>
        </div>
        {report && (
          <div className="fsck-results">
            <div className={`status-summary status-${report.status.toLowerCase()}`}>
              健康状态：<strong>{report.status}</strong>（已检查 {report.checked} 项，发现 {report.errors?.length || 0} 处异常）
            </div>
            {report.errors?.length > 0 && (
              <div className="error-list">
                <h4>检测到的异常列表：</h4>
                {report.errors.map((err, idx) => (
                  <div key={idx} className="error-item">
                    <div><span className="badge badge-danger">[{err.type}]</span> {err.file_path || `Revision ${err.revision_id}`}</div>
                    {err.type === 'HASH_MISMATCH' && (
                      <div className="conflict-actions">
                        <span>哈希不一致，请选择决议：</span>
                        <button className="btn-small" onClick={() => handleResolveConflict(err.journal_id, 'SQLITE')}>以数据库为准（覆盖文件）</button>
                        <button className="btn-small" onClick={() => handleResolveConflict(err.journal_id, 'FILE')}>以文件为准（更新数据库）</button>
                        <button className="btn-small btn-secondary" onClick={() => handleResolveConflict(err.journal_id, 'DUAL')}>保留两份（创建分支版本）</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
