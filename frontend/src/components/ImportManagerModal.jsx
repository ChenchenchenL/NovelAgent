import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export function ImportManagerModal({ onClose, onImportCompleted }) {
  const [sourcePath, setSourcePath] = useState('')
  const [batchSize, setBatchSize] = useState(10)
  const [autoExtract, setAutoExtract] = useState(false)
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const loadJobs = async () => {
    try {
      setJobs(await api.listImportJobs())
    } catch (e) {
      setMsg(e.message)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [])

  const handleStartImport = async (e) => {
    e.preventDefault()
    if (!sourcePath) return
    setLoading(true)
    try {
      await api.createImportJob({ source_path: sourcePath, batch_size: Number(batchSize), auto_extract: autoExtract })
      setMsg('导入任务已启动')
      await loadJobs()
      if (onImportCompleted) onImportCompleted()
    } catch (err) {
      setMsg(`启动失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (jobId, action) => {
    try {
      if (action === 'pause') await api.pauseImportJob(jobId)
      else if (action === 'resume') await api.resumeImportJob(jobId)
      else if (action === 'retry') await api.retryImportJob(jobId)
      else if (action === 'cancel') await api.cancelImportJob(jobId)
      await loadJobs()
    } catch (err) {
      setMsg(err.message)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content import-modal">
        <div className="modal-header">
          <h3>📦 存量作品批量导入</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>
        {msg && <div className="notice-bar">{msg}</div>}
        <form onSubmit={handleStartImport} className="import-form">
          <div className="form-group">
            <label>源文档目录绝对路径</label>
            <input type="text" value={sourcePath} placeholder="/path/to/novel_files" onChange={(e) => setSourcePath(e.target.value)} required />
          </div>
          <div className="form-row">
            <label>每批文件数：<input type="number" min="1" max="100" value={batchSize} onChange={(e) => setBatchSize(e.target.value)} /></label>
            <label><input type="checkbox" checked={autoExtract} onChange={(e) => setAutoExtract(e.target.checked)} /> 导入后自动逆向抽取</label>
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>{loading ? '启动中...' : '🚀 开始批量导入'}</button>
        </form>
        <div className="import-jobs-list">
          <h4>最近导入任务</h4>
          {jobs.length === 0 ? <p className="empty">暂无导入记录</p> : (
            <ul>
              {jobs.map((j) => (
                <li key={j.id} className="job-item">
                  <div><strong>#{j.id}</strong> {j.source_path} <span className={`badge badge-${j.status.toLowerCase()}`}>{j.status}</span> ({j.checkpoint}/{j.total_batches} 批)</div>
                  <div className="job-actions">
                    {j.status === 'RUNNING' && <button className="btn-small" onClick={() => handleAction(j.id, 'pause')}>暂停</button>}
                    {j.status === 'PAUSED' && <button className="btn-small" onClick={() => handleAction(j.id, 'resume')}>继续</button>}
                    {j.status === 'FAILED' && <button className="btn-small" onClick={() => handleAction(j.id, 'retry')}>重试</button>}
                    {j.status !== 'COMPLETED' && j.status !== 'CANCELLED' && <button className="btn-small btn-danger" onClick={() => handleAction(j.id, 'cancel')}>取消</button>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
