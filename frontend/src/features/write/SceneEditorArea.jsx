import React from 'react'
import { MarkdownEditor } from '../../components/MarkdownEditor'
import { PreviewPanel } from '../../components/PreviewPanel'
import { ArbitrationWorkbench } from '../../components/ArbitrationWorkbench'
import { RevisionHistory } from '../../components/RevisionHistory'
import { RevisionDiff } from '../../components/RevisionDiff'
import { ConflictDialog } from '../../components/ConflictDialog'

export function SceneEditorArea({
  scene,
  activeTab,
  draftContent,
  viewingRevision,
  setViewingRevision,
  isSaving,
  saveError,
  hasSnapshot,
  canUndo,
  canRedo,
  diff,
  setDiff,
  conflict,
  setConflict,
  revisions,
  onContentChange,
  onUndo,
  onRedo,
  onSnapshot,
  onRestore,
  onReset,
  onRetrySave,
  onViewRevision,
  onDiffRevision,
}) {
  const revisionBanner = viewingRevision && (
    <div className="history-preview-banner">
      <span>正在预览历史版本 #{viewingRevision.id}（只读模式）</span>
      <button onClick={() => setViewingRevision(null)}>返回当前草稿</button>
    </div>
  )

  return (
    <div className="scene-editor-canvas">
      {activeTab === 'editor' && (
        <MarkdownEditor
          draftContent={viewingRevision ? viewingRevision.content : draftContent}
          isSaving={isSaving}
          saveError={saveError}
          hasSnapshot={hasSnapshot}
          canUndo={canUndo}
          canRedo={canRedo}
          readOnly={Boolean(viewingRevision)}
          banner={revisionBanner}
          onContentChange={onContentChange}
          onUndo={onUndo}
          onRedo={onRedo}
          onSnapshot={onSnapshot}
          onRestore={onRestore}
          onReset={onReset}
          onRetrySave={onRetrySave}
        />
      )}

      {activeTab === 'preview' && (
        <PreviewPanel content={draftContent} />
      )}

      {activeTab === 'arbitration' && (
        <ArbitrationWorkbench sceneId={scene?.id} />
      )}

      {activeTab === 'revisions' && (
        <RevisionHistory
          revisions={revisions}
          onViewRevision={onViewRevision}
          onDiffRevision={onDiffRevision}
        />
      )}

      {diff && (
        <RevisionDiff diff={diff} onClose={() => setDiff(null)} />
      )}

      {conflict && (
        <ConflictDialog
          conflict={conflict}
          onReloadCanon={() => { onReset(); setConflict(null) }}
          onKeepDraft={() => setConflict(null)}
          onCancel={() => setConflict(null)}
        />
      )}
    </div>
  )
}
