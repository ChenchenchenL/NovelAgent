import React, { useEffect, useState } from 'react'
import { ContractPanel } from './ContractPanel'
import { RevisionHistory } from './RevisionHistory'
import { MarkdownEditor } from './MarkdownEditor'
import { PreviewPanel } from './PreviewPanel'
import { RevisionDiff } from './RevisionDiff'
import { ConflictDialog } from './ConflictDialog'
import { useWorkspace } from '../hooks/useWorkspace'
import { useUndoRedo } from '../hooks/useUndoRedo'
import { api } from '../api/client'

export function SceneEditor({
  scene,
  tab,
  setTab,
  viewingRevision,
  setViewingRevision,
  revisions,
  busy,
  onChangeSceneStatus,
  onSaveScene,
  onViewRevision,
}) {
  const [diff, setDiff] = useState(null)
  const [conflict, setConflict] = useState(null)
  const ws = useWorkspace(scene?.id, scene?.content || '')
  const ur = useUndoRedo()

  useEffect(() => {
    ur.resetStacks()
  }, [scene?.id])

  const handleContentChange = (val, cursor) => {
    ur.pushState(ws.draftContent)
    ws.onDraftChange(val, cursor)
  }

  const handleDiff = async (revId, againstId) => {
    if (!scene?.id) return
    setDiff(await api.getDiff(scene.id, revId, againstId))
  }

  const handleSave = async () => {
    try {
      await onSaveScene(ws.draftContent)
    } catch (err) {
      if (err.status === 409 || err.message?.includes('冲突') || err.message?.includes('CONFLICT')) {
        let conflictData = { current_revision_id: '已更新', workspace_base_revision_id: '旧版' }
        try {
          if (typeof err.message === 'string' && err.message.startsWith('{')) conflictData = JSON.parse(err.message)
        } catch {}
        setConflict(conflictData)
      }
    }
  }

  const revisionBanner = viewingRevision ? (
    <div className="revision-banner">
      <span>正在预览历史版本 #{viewingRevision.id}（{viewingRevision.created_at}）</span>
      <button onClick={() => setViewingRevision(null)}>返回当前版本</button>
    </div>
  ) : null

  return (
    <section className="editor panel">
      <div className="panel-title">
        <div className="scene-meta">
          <strong>{scene?.title || '未选择场景'}</strong>
          {scene && (
            <div className="scene-tags">
              <span className="tag">POV: {scene.pov || '未设'}</span>
              <span className="tag">地点: {scene.location || '未设'}</span>
              <select className="status-select" value={scene.status} onChange={(e) => onChangeSceneStatus(scene.id, e.target.value)}>
                <option value="PLANNED">PLANNED</option>
                <option value="WRITING">WRITING</option>
                <option value="PARTIALLY_ACCEPTED">PARTIALLY_ACCEPTED</option>
                <option value="EXTRACTION_PENDING">EXTRACTION_PENDING</option>
                <option value="SCENE_ACCEPTED">SCENE_ACCEPTED</option>
              </select>
            </div>
          )}
        </div>
        <div className="actions">
          <button className={tab === 'editor' ? 'primary' : ''} onClick={() => setTab('editor')}>编辑</button>
          <button className={tab === 'preview' ? 'primary' : ''} onClick={() => setTab('preview')}>Markdown预览</button>
          <button className={tab === 'contracts' ? 'primary' : ''} onClick={() => setTab('contracts')} disabled={!scene}>契约</button>
          <button className={tab === 'revisions' ? 'primary' : ''} onClick={() => setTab('revisions')} disabled={!scene}>版本({revisions.length})</button>
          <button className="primary" onClick={handleSave} disabled={!scene || busy || viewingRevision !== null}>采纳为正典</button>
        </div>
      </div>

      {tab === 'editor' && (
        <MarkdownEditor
          draftContent={viewingRevision ? viewingRevision.content : ws.draftContent}
          isSaving={ws.isSaving}
          hasSnapshot={ws.hasSnapshot}
          canUndo={ur.canUndo}
          canRedo={ur.canRedo}
          readOnly={Boolean(viewingRevision)}
          banner={revisionBanner}
          onContentChange={handleContentChange}
          onUndo={() => ur.undo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onRedo={() => ur.redo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onSnapshot={ws.takeSnapshot}
          onRestore={ws.restoreSnapshot}
          onReset={ws.resetWorkspace}
        />
      )}

      {tab === 'preview' && <PreviewPanel content={ws.draftContent} />}
      {tab === 'contracts' && <ContractPanel scene={scene} />}
      {tab === 'revisions' && <RevisionHistory revisions={revisions} onViewRevision={onViewRevision} onDiffRevision={handleDiff} />}
      {diff && <RevisionDiff diff={diff} onClose={() => setDiff(null)} />}
      {conflict && <ConflictDialog conflict={conflict} onReloadCanon={() => { ws.resetWorkspace(); setConflict(null) }} onKeepDraft={() => setConflict(null)} onCancel={() => setConflict(null)} />}
    </section>
  )
}
