import React, { useEffect, useState } from 'react'
import { SceneHeader } from './SceneHeader'
import { GenerationProgress } from './GenerationProgress'
import { TaskList } from './TaskList'
import { ContractPanel } from './ContractPanel'
import { RevisionHistory } from './RevisionHistory'
import { MarkdownEditor } from './MarkdownEditor'
import { PreviewPanel } from './PreviewPanel'
import { RevisionDiff } from './RevisionDiff'
import { ConflictDialog } from './ConflictDialog'
import { ArbitrationWorkbench } from './ArbitrationWorkbench'
import { AgentThoughtStream } from '../features/agent/AgentThoughtStream'
import { useWorkspace } from '../hooks/useWorkspace'
import { useUndoRedo } from '../hooks/useUndoRedo'
import { useGeneration } from '../hooks/useGeneration'
import { api } from '../api/client'

export function SceneEditor({
  scene, tab, setTab, viewingRevision, setViewingRevision,
  revisions, busy, onChangeSceneStatus, onSaveScene, onViewRevision,
  thoughtProcess,
}) {
  const [diff, setDiff] = useState(null)
  const [conflict, setConflict] = useState(null)
  const ws = useWorkspace(scene?.id, scene?.content || '')
  const ur = useUndoRedo()

  const gen = useGeneration(scene?.id, (newContent) => {
    if (newContent) ws.onDraftChange(newContent)
  })

  useEffect(() => { ur.resetStacks() }, [scene?.id])

  const handleContentChange = (val, cursor) => {
    ur.pushState(ws.draftContent)
    ws.onDraftChange(val, cursor)
  }

  const handleDiff = async (revId, againstId) => {
    if (scene?.id) setDiff(await api.getDiff(scene.id, revId, againstId))
  }

  const handleSave = async () => {
    try {
      await onSaveScene(ws.draftContent)
    } catch (err) {
      let conflictData = { current_revision_id: '已更新', workspace_base_revision_id: '旧版' }
      try {
        if (typeof err.message === 'string' && err.message.startsWith('{')) conflictData = JSON.parse(err.message)
      } catch {}
      setConflict(conflictData)
    }
  }

  const revisionBanner = viewingRevision && (
    <div className="history-preview-banner">
      <span>正在预览历史版本 #{viewingRevision.id}（只读模式）</span>
      <button onClick={() => setViewingRevision(null)}>返回当前草稿</button>
    </div>
  )

  return (
    <section className="editor-panel">
      <SceneHeader
        scene={scene} tab={tab} setTab={setTab} revisionsCount={revisions.length}
        busy={busy} viewingRevision={viewingRevision} generating={gen.generating}
        onChangeSceneStatus={onChangeSceneStatus} onSave={handleSave} onGenerate={gen.startGeneration}
      />
      <AgentThoughtStream thoughtProcess={thoughtProcess} />
      <GenerationProgress
        generating={gen.generating} statusText={gen.statusText}
        streamingText={gen.streamingText} onCancel={gen.cancelGeneration}
      />
      {tab === 'editor' && (
        <MarkdownEditor
          draftContent={viewingRevision ? viewingRevision.content : ws.draftContent}
          isSaving={ws.isSaving} saveError={ws.saveError} hasSnapshot={ws.hasSnapshot}
          canUndo={ur.canUndo} canRedo={ur.canRedo} readOnly={Boolean(viewingRevision)}
          banner={revisionBanner} onContentChange={handleContentChange}
          onUndo={() => ur.undo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onRedo={() => ur.redo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onSnapshot={ws.takeSnapshot} onRestore={ws.restoreSnapshot} onReset={ws.resetWorkspace}
          onRetrySave={() => ws.saveWorkspace(ws.draftContent)}
        />
      )}
      {tab === 'preview' && <PreviewPanel content={ws.draftContent} />}
      {tab === 'arbitration' && <ArbitrationWorkbench sceneId={scene?.id} />}
      {tab === 'contracts' && <ContractPanel scene={scene} />}
      {tab === 'revisions' && <RevisionHistory revisions={revisions} onViewRevision={onViewRevision} onDiffRevision={handleDiff} />}
      {diff && <RevisionDiff diff={diff} onClose={() => setDiff(null)} />}
      {conflict && <ConflictDialog conflict={conflict} onReloadCanon={() => { ws.resetWorkspace(); setConflict(null) }} onKeepDraft={() => setConflict(null)} onCancel={() => setConflict(null)} />}
      <TaskList runs={gen.runs} />
    </section>
  )
}
