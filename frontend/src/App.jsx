import React, { useState } from 'react'
import { AppHeader } from './layout/AppHeader'
import { WriteWorkspace } from './features/write/WriteWorkspace'
import { NoticeToast } from './layout/NoticeToast'
import { AutoPlanModal } from './features/agent/AutoPlanModal'
import { OutlineModal } from './features/plan/OutlineModal'
import { ProjectSetupModal } from './features/settings/ProjectSetupModal'
import { useProject } from './hooks/useProject'
import { useScene } from './hooks/useScene'
import { useSession } from './hooks/useSession'
import { api } from './api/client'

export default function App() {
  const [notice, setNotice] = useState('NovelAgent 小说主创工作台准备就绪')
  const [selectedChapterId, setSelectedChapterId] = useState(null)
  const [selectedChapter, setSelectedChapter] = useState(null)
  const [showAutoPlan, setShowAutoPlan] = useState(false)
  const [showOutline, setShowOutline] = useState(false)
  const [showProjectModal, setShowProjectModal] = useState(false)

  useSession(setNotice)
  const projectState = useProject(setNotice)
  const sceneState = useScene(setNotice, projectState.refreshTree)

  projectState.handleCreate = async (type, parentId = null) => {
    const title = window.prompt(`输入${type}名称：`, `新${type}`)
    if (!title) return
    try {
      if (type === '卷') await api.createVolume(title)
      else if (type === '章节') {
        const res = await api.createChapter({ title, volume_id: parentId })
        handleSelectChapter(res.id)
      } else if (type === '场景') {
        const res = await api.createScene(parentId, { title })
        await sceneState.selectScene(res.id)
      }
      await projectState.refreshTree()
      setNotice(`已创建${type}：${title}`)
    } catch (err) { setNotice(err.message) }
  }

  const handleSelectChapter = async (id) => {
    setSelectedChapterId(id)
    try {
      setSelectedChapter(await api.getChapter(id))
    } catch (err) { setNotice(err.message) }
  }

  return (
    <div className="app-layout">
      <AppHeader
        projectName={projectState.project?.name}
        currentPath={projectState.currentPath}
        selectedSceneTitle={sceneState.scene?.title}
        onOpenProjectSettings={() => setShowProjectModal(true)}
        onOpenOutlineModal={() => setShowOutline(true)}
        onQuickSave={() => sceneState.saveScene()}
        canSave={Boolean(sceneState.scene)}
        isSaving={sceneState.busy}
      />
      <main className="app-main-viewport">
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
          onSelectChapter={handleSelectChapter}
          onSelectScene={sceneState.selectScene}
          onSaveScene={sceneState.saveScene}
          onViewRevision={sceneState.viewRevision}
          onOpenAutoPlan={() => setShowAutoPlan(true)}
          onRefreshTree={projectState.refreshTree}
        />
      </main>

      <NoticeToast notice={notice} onDismiss={() => setNotice('')} />

      <AutoPlanModal
        isOpen={showAutoPlan}
        onClose={() => setShowAutoPlan(false)}
        onPlanCompleted={async () => {
          await projectState.refreshTree()
          setShowAutoPlan(false)
          setNotice('全书大纲与设定推演已完成')
        }}
      />

      <OutlineModal
        isOpen={showOutline}
        onClose={() => setShowOutline(false)}
        currentSceneId={sceneState.scene?.id}
        onOpenAutoPlan={() => {
          setShowOutline(false)
          setShowAutoPlan(true)
        }}
      />

      <ProjectSetupModal
        isOpen={showProjectModal}
        onClose={() => setShowProjectModal(false)}
        currentPath={projectState.currentPath}
        setCurrentPath={projectState.setCurrentPath}
        historyPaths={projectState.historyPaths}
        onOpenProject={projectState.openProject}
      />
    </div>
  )
}
