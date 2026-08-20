import { useState } from 'react'
import { api } from './api/client'
import { ChapterControl } from './components/ChapterControl'
import { ChapterTree } from './components/ChapterTree'
import { SceneEditor } from './components/SceneEditor'
import { SetupPanel } from './components/SetupPanel'
import { Topbar } from './components/Topbar'
import { useProject } from './hooks/useProject'
import { useScene } from './hooks/useScene'
import { useSession } from './hooks/useSession'

export default function App() {
  const [notice, setNotice] = useState('准备就绪')
  const [selectedChapterId, setSelectedChapterId] = useState(null)
  const [selectedChapter, setSelectedChapter] = useState(null)
  const [tab, setTab] = useState('editor')

  useSession(setNotice)
  const projectState = useProject(setNotice)
  const sceneState = useScene(setNotice, projectState.refreshTree)

  const handleSelectChapter = async (chapterId) => {
    setSelectedChapterId(chapterId)
    try {
      setSelectedChapter(await api.getChapter(chapterId))
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCreateVolume = async () => {
    const title = window.prompt('输入卷标题：', '新卷')
    if (!title) return
    try {
      await api.createVolume(title)
      await projectState.refreshTree()
      setNotice(`已创建卷：${title}`)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCreateChapter = async (volumeId = null) => {
    const title = window.prompt('输入章节标题：', '新章节')
    if (!title) return
    try {
      const res = await api.createChapter({ title, volume_id: volumeId })
      await projectState.refreshTree()
      setNotice(`已创建章节：${title}`)
      handleSelectChapter(res.id)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCreateScene = async (chapterId) => {
    const title = window.prompt('输入场景标题：', '新场景')
    if (!title) return
    try {
      const res = await api.createScene(chapterId, { title })
      await projectState.refreshTree()
      await sceneState.selectScene(res.id)
      setNotice(`已创建场景：${title}`)
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
    <main className="app-shell">
      <Topbar notice={notice} />
      <SetupPanel
        currentPath={projectState.currentPath}
        setCurrentPath={projectState.setCurrentPath}
        historyPaths={projectState.historyPaths}
        setHistoryPaths={projectState.setHistoryPaths}
        onChooseDirectory={projectState.chooseDirectory}
        onOpenProject={projectState.openProject}
        disabled={!projectState.currentPath}
      />
      <div className="workspace">
        <ChapterTree
          tree={projectState.tree}
          project={projectState.project}
          selectedChapterId={selectedChapterId}
          selectedSceneId={sceneState.scene?.id}
          onCreateVolume={handleCreateVolume}
          onCreateChapter={handleCreateChapter}
          onCreateScene={handleCreateScene}
          onSelectChapter={handleSelectChapter}
          onSelectScene={sceneState.selectScene}
        />
        <SceneEditor
          scene={sceneState.scene}
          tab={tab}
          setTab={setTab}
          viewingRevision={sceneState.viewingRevision}
          setViewingRevision={sceneState.setViewingRevision}
          revisions={sceneState.revisions}
          busy={sceneState.busy}
          onChangeSceneStatus={sceneState.changeSceneStatus}
          onSaveScene={sceneState.saveScene}
          onViewRevision={sceneState.viewRevision}
        />
        <ChapterControl selectedChapter={selectedChapter} onChangeStatus={handleChangeChapterStatus} />
      </div>
    </main>
  )
}
