import React, { useState, useEffect } from 'react'
import { ChapterTree } from '../../components/ChapterTree'
import { SceneBreadcrumb } from './SceneBreadcrumb'
import { SceneEditorArea } from './SceneEditorArea'
import { InspectorPanel } from './InspectorPanel'
import { useWorkspace } from '../../hooks/useWorkspace'
import { useUndoRedo } from '../../hooks/useUndoRedo'
import { useGeneration } from '../../hooks/useGeneration'
import { api } from '../../api/client'

export function WriteWorkspace({
  project,
  tree,
  selectedChapterId,
  selectedChapter,
  scene,
  revisions,
  viewingRevision,
  setViewingRevision,
  busy,
  onCreateVolume,
  onCreateChapter,
  onCreateScene,
  onSelectChapter,
  onSelectScene,
  onChangeSceneStatus,
  onChangeChapterStatus,
  onSaveScene,
  onViewRevision,
}) {
  const [tab, setTab] = useState('editor')
  const [diff, setDiff] = useState(null)
  const [conflict, setConflict] = useState(null)

  const ws = useWorkspace(scene?.id, scene?.content || '')
  const ur = useUndoRedo()
  const gen = useGeneration(scene?.id, (content) => content && ws.onDraftChange(content))

  useEffect(() => { ur.resetStacks() }, [scene?.id])

  const handleContentChange = (val, cursor) => {
    ur.pushState(ws.draftContent)
    ws.onDraftChange(val, cursor)
  }

  const handleSave = async () => {
    try {
      await onSaveScene(ws.draftContent)
    } catch (err) {
      let data = { current_revision_id: '已更新', workspace_base_revision_id: '旧版' }
      try {
        if (typeof err.message === 'string' && err.message.startsWith('{')) data = JSON.parse(err.message)
      } catch {}
      setConflict(data)
    }
  }

  const handleApplyStreaming = (text) => {
    if (!text) return
    const updated = ws.draftContent ? `${ws.draftContent}\n\n${text}` : text
    handleContentChange(updated, updated.length)
  }

  return (
    <div className="write-workspace-grid">
      <ChapterTree
        tree={tree} project={project}
        selectedChapterId={selectedChapterId} selectedSceneId={scene?.id}
        onCreateVolume={onCreateVolume} onCreateChapter={onCreateChapter} onCreateScene={onCreateScene}
        onSelectChapter={onSelectChapter} onSelectScene={onSelectScene}
      />
      <section className="writing-canvas-panel">
        <SceneBreadcrumb
          scene={scene} activeTab={tab} onTabChange={setTab}
          revisionsCount={revisions.length} onChangeSceneStatus={onChangeSceneStatus}
          onSaveScene={handleSave} busy={busy} viewingRevision={viewingRevision}
        />
        <SceneEditorArea
          scene={scene} activeTab={tab} draftContent={ws.draftContent}
          viewingRevision={viewingRevision} setViewingRevision={setViewingRevision}
          isSaving={ws.isSaving} saveError={ws.saveError} hasSnapshot={ws.hasSnapshot}
          canUndo={ur.canUndo} canRedo={ur.canRedo} diff={diff} setDiff={setDiff}
          conflict={conflict} setConflict={setConflict} revisions={revisions}
          onContentChange={handleContentChange}
          onUndo={() => ur.undo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onRedo={() => ur.redo(ws.draftContent, (v) => ws.onDraftChange(v))}
          onSnapshot={ws.takeSnapshot} onRestore={ws.restoreSnapshot} onReset={ws.resetWorkspace}
          onRetrySave={() => ws.saveWorkspace(ws.draftContent)}
          onViewRevision={onViewRevision}
          onDiffRevision={async (revId, againstId) => scene?.id && setDiff(await api.getDiff(scene.id, revId, againstId))}
        />
      </section>
      <InspectorPanel
        scene={scene} selectedChapter={selectedChapter}
        generating={gen.generating} statusText={gen.statusText}
        streamingText={gen.streamingText} runs={gen.runs}
        onStartGeneration={gen.startGeneration} onCancelGeneration={gen.cancelGeneration}
        onApplyStreaming={handleApplyStreaming} onChangeChapterStatus={onChangeChapterStatus}
      />
    </div>
  )
}
