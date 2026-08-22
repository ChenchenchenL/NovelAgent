import React from 'react'
import { VIEWS } from './ActivityBar'
import { WriteWorkspace } from '../features/write/WriteWorkspace'
import { PlanView } from '../features/plan/PlanView'
import { CodexView } from '../features/codex/CodexView'
import { SettingsView } from '../features/settings/SettingsView'

export function ViewRouter({
  activeView,
  projectState,
  sceneState,
  selectedChapterId,
  selectedChapter,
  onSelectChapter,
  onChangeChapterStatus,
  onOpenAutoPlan,
}) {
  if (activeView === VIEWS.WRITE) {
    return (
      <WriteWorkspace
        project={projectState.project}
        tree={projectState.tree}
        selectedChapterId={selectedChapterId}
        selectedChapter={selectedChapter}
        scene={sceneState.scene}
        revisions={sceneState.revisions}
        viewingRevision={sceneState.viewingRevision}
        setViewingRevision={sceneState.setViewingRevision}
        busy={sceneState.busy}
        onCreateVolume={() => projectState.handleCreate?.('卷')}
        onCreateChapter={(vId) => projectState.handleCreate?.('章节', vId)}
        onCreateScene={(cId) => projectState.handleCreate?.('场景', cId)}
        onSelectChapter={onSelectChapter}
        onSelectScene={sceneState.selectScene}
        onChangeSceneStatus={sceneState.changeSceneStatus}
        onChangeChapterStatus={onChangeChapterStatus}
        onSaveScene={sceneState.saveScene}
        onViewRevision={sceneState.viewRevision}
        onOpenNewStory={onOpenAutoPlan}
        onRefreshTree={projectState.refreshTree}
      />
    )
  }

  if (activeView === VIEWS.PLAN) return <PlanView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.CODEX) return <CodexView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.SETTINGS) {
    return (
      <SettingsView
        currentPath={projectState.currentPath}
        setCurrentPath={projectState.setCurrentPath}
        historyPaths={projectState.historyPaths}
        setHistoryPaths={projectState.setHistoryPaths}
        onChooseDirectory={projectState.chooseDirectory}
        onOpenProject={projectState.openProject}
        onRefreshTree={projectState.refreshTree}
      />
    )
  }

  return null
}
