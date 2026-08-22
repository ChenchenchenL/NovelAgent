import React from 'react'
import { VIEWS } from './ActivityBar'
import { WriteWorkspace } from '../features/write/WriteWorkspace'
import { PlanView } from '../features/plan/PlanView'
import { CodexView } from '../features/codex/CodexView'
import { SearchView } from '../features/search/SearchView'
import { QualityView } from '../features/quality/QualityView'
import { GlobalView } from '../features/global/GlobalView'
import { SettingsView } from '../features/settings/SettingsView'

export function ViewRouter({
  activeView,
  projectState,
  sceneState,
  selectedChapterId,
  selectedChapter,
  onCreateVolume,
  onCreateChapter,
  onCreateScene,
  onSelectChapter,
  onChangeChapterStatus,
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
        onCreateVolume={onCreateVolume}
        onCreateChapter={onCreateChapter}
        onCreateScene={onCreateScene}
        onSelectChapter={onSelectChapter}
        onSelectScene={sceneState.selectScene}
        onChangeSceneStatus={sceneState.changeSceneStatus}
        onChangeChapterStatus={onChangeChapterStatus}
        onSaveScene={sceneState.saveScene}
        onViewRevision={sceneState.viewRevision}
      />
    )
  }
  if (activeView === VIEWS.PLAN) return <PlanView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.CODEX) return <CodexView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.SEARCH) return <SearchView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.QUALITY) return <QualityView currentSceneId={sceneState.scene?.id} />
  if (activeView === VIEWS.GLOBAL) return <GlobalView />
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
