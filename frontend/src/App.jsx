import React, { useState } from 'react'
import { ActivityBar, VIEWS } from './layout/ActivityBar'
import { AppHeader } from './layout/AppHeader'
import { ViewRouter } from './layout/ViewRouter'
import { NoticeToast } from './layout/NoticeToast'
import { useProject } from './hooks/useProject'
import { useScene } from './hooks/useScene'
import { useSession } from './hooks/useSession'
import { api } from './api/client'

export default function App() {
  const [activeView, setActiveView] = useState(VIEWS.WRITE)
  const [notice, setNotice] = useState('NovelAgent 正典系统准备就绪')
  const [selectedChapterId, setSelectedChapterId] = useState(null)
  const [selectedChapter, setSelectedChapter] = useState(null)

  useSession(setNotice)
  const projectState = useProject(setNotice)
  const sceneState = useScene(setNotice, projectState.refreshTree)

  const handleSelectChapter = async (id) => {
    setSelectedChapterId(id)
    try {
      setSelectedChapter(await api.getChapter(id))
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCreate = async (type, parentId = null) => {
    const title = window.prompt(`输入${type}标题：`, `新${type}`)
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
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleChangeChapterStatus = async (chapterId, status) => {
    try {
      await api.updateChapterStatus(chapterId, status)
      await handleSelectChapter(chapterId)
      await projectState.refreshTree()
      setNotice(`章节状态已变更为：${status}`)
    } catch (err) {
      setNotice(`状态变更被阻断：${err.message}`)
    }
  }

  return (
    <div className="app-layout">
      <ActivityBar activeView={activeView} onViewChange={setActiveView} />
      <div className="app-main-viewport">
        <AppHeader
          projectName={projectState.project?.name}
          currentPath={projectState.currentPath}
          selectedSceneTitle={sceneState.scene?.title}
          notice={notice}
          onOpenSettings={() => setActiveView(VIEWS.SETTINGS)}
          onQuickSave={() => sceneState.saveScene()}
          canSave={Boolean(sceneState.scene)}
          isSaving={sceneState.busy}
        />
        <main className="app-view-body">
          <ViewRouter
            activeView={activeView}
            projectState={projectState}
            sceneState={sceneState}
            selectedChapterId={selectedChapterId}
            selectedChapter={selectedChapter}
            onCreateVolume={() => handleCreate('卷')}
            onCreateChapter={(vId) => handleCreate('章节', vId)}
            onCreateScene={(cId) => handleCreate('场景', cId)}
            onSelectChapter={handleSelectChapter}
            onChangeChapterStatus={handleChangeChapterStatus}
          />
        </main>
        <NoticeToast notice={notice} onDismiss={() => setNotice('')} />
      </div>
    </div>
  )
}
