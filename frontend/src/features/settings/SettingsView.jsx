import React, { useState } from 'react'
import { SetupPanel } from '../../components/SetupPanel'
import { ModelConfigPanel } from '../../components/ModelConfigPanel'
import { ImportManagerModal } from '../../components/ImportManagerModal'
import { FsckModal } from '../../components/FsckModal'
import { BackupExportModal } from '../../components/BackupExportModal'

export function SettingsView({
  currentPath,
  setCurrentPath,
  historyPaths,
  setHistoryPaths,
  onChooseDirectory,
  onOpenProject,
  onRefreshTree,
}) {
  const [activeTab, setActiveTab] = useState('model')
  const [showImport, setShowImport] = useState(false)
  const [showFsck, setShowFsck] = useState(false)
  const [showBackup, setShowBackup] = useState(false)

  const tabs = [
    { id: 'model', label: '模型网关与分级' },
    { id: 'project', label: '目录与项目授权' },
    { id: 'tools', label: '导入、自愈与备份' },
  ]

  return (
    <div className="view-container">
      <div className="view-header">
        <div className="view-title-group">
          <h2>项目配置与系统工具箱 (Settings & Tools)</h2>
          <p className="view-subtitle">OpenAI-compatible 模型路由分级、安全 Keyring 密钥、本地目录授权、存量文件导入、FSCK 自愈与备份。</p>
        </div>
        <div className="view-tabs-bar">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`view-tab-btn ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="view-content-card">
        {activeTab === 'model' && <ModelConfigPanel />}
        {activeTab === 'project' && (
          <SetupPanel
            currentPath={currentPath}
            setCurrentPath={setCurrentPath}
            historyPaths={historyPaths}
            setHistoryPaths={setHistoryPaths}
            onChooseDirectory={onChooseDirectory}
            onOpenProject={onOpenProject}
            disabled={!currentPath}
          />
        )}
        {activeTab === 'tools' && (
          <div className="tools-dashboard-grid">
            <div className="tool-card">
              <div className="tool-badge-label">存量导入</div>
              <h4>作品批量导入</h4>
              <p>支持 Markdown/TXT/JSON/YAML 分批导入与断点恢复。</p>
              <button className="btn-primary" onClick={() => setShowImport(true)}>打开批量导入器</button>
            </div>
            <div className="tool-card">
              <div className="tool-badge-label">自愈检查</div>
              <h4>FSCK 跨介质一致性检查</h4>
              <p>诊断并自动修复 SQLite 数据库、正文文件与派生索引不一致。</p>
              <button className="btn-primary" onClick={() => setShowFsck(true)}>运行 FSCK 自愈检查</button>
            </div>
            <div className="tool-card">
              <div className="tool-badge-label">归档管理</div>
              <h4>备份、全书导出与还原</h4>
              <p>一键打包当前正典数据库与正文版本为 .tar.gz 归档。</p>
              <button className="btn-primary" onClick={() => setShowBackup(true)}>打开备份中心</button>
            </div>
          </div>
        )}
      </div>

      {showImport && <ImportManagerModal onClose={() => setShowImport(false)} onImportCompleted={onRefreshTree} />}
      {showFsck && <FsckModal onClose={() => setShowFsck(false)} />}
      {showBackup && <BackupExportModal onClose={() => setShowBackup(false)} />}
    </div>
  )
}
