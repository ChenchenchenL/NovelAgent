import React, { useState, useEffect } from 'react'
import { ChapterSidebar } from './ChapterSidebar'
import { SceneBreadcrumb } from './SceneBreadcrumb'
import { SceneEditorArea } from './SceneEditorArea'
import { InspectorPanel } from './InspectorPanel'
import { useWorkspace } from '../../hooks/useWorkspace'
import { useUndoRedo } from '../../hooks/useUndoRedo'
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
  onSaveScene,
  onViewRevision,
  onOpenAutoPlan,
  onRefreshTree,
}) {
  const [tab, setTab] = useState('editor')
  const [diff, setDiff] = useState(null)
  const [conflict, setConflict] = useState(null)

  const ws = useWorkspace(scene?.id, scene?.content || '')
  const ur = useUndoRedo()

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

  const handleSceneUpdated = (res) => {
    if (res?.content) handleContentChange(res.content, res.content.length)
  }

  const handleAdvanced = async () => {
    try {
      const res = await api.autoAdvanceScene()
      if (res?.scene_id) {
        await onSelectScene(res.scene_id)
        if (res.content) handleContentChange(res.content, res.content.length)
        if (onRefreshTree) await onRefreshTree()
      }
    } catch (err) {
      alert(`自动推进失败: ${err.message}`)
    }
  }

  return (
    <div className="write-workspace-grid">
      <ChapterSidebar
        tree={tree} project={project}
        selectedChapterId={selectedChapterId} selectedSceneId={scene?.id}
        onCreateVolume={onCreateVolume} onCreateChapter={onCreateChapter} onCreateScene={onCreateScene}
        onSelectChapter={onSelectChapter} onSelectScene={onSelectScene}
        onOpenAutoPlan={onOpenAutoPlan}
      />
      <section className="writing-canvas-panel">
        <SceneBreadcrumb
          scene={scene} activeTab={tab} onTabChange={setTab}
          draftContent={ws.draftContent} revisionsCount={revisions.length}
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
          onDiffRevision={async (rId, aId) => scene?.id && setDiff(await api.getDiff(scene.id, rId, aId))}
        />
      </section>
      <InspectorPanel
        scene={scene}
        onApplyStreaming={(text) => handleContentChange(ws.draftContent ? `${ws.draftContent}\n\n${text}` : text)}
        onSceneContentUpdated={handleSceneUpdated}
        onAdvanceCompleted={handleAdvanced}
      />
    </div>
  )
}
