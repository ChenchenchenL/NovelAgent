import { useState } from 'react'
import { api } from './api/client'
import { ChapterControl } from './components/ChapterControl'
import { ChapterTree } from './components/ChapterTree'
import { SceneEditor } from './components/SceneEditor'
import { SetupPanel } from './components/SetupPanel'
import { ModelConfigPanel } from './components/ModelConfigPanel'
import { Topbar } from './components/Topbar'
import { useProject } from './hooks/useProject'
import { useScene } from './hooks/useScene'
import { useSession } from './hooks/useSession'

export default function App() {
  const [notice, setNotice] = useState('准备就绪')
  const [selectedChapterId, setSelectedChapterId] = useState(null)
  const [selectedChapter, setSelectedChapter] = useState(null)
  const [tab, setTab] = useState('editor')
  const [showModelConfig, setShowModelConfig] = useState(false)

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
    <main className="app-shell">
      <Topbar
        notice={notice}
        showModelConfig={showModelConfig}
        onToggleModelConfig={() => setShowModelConfig(!showModelConfig)}
      />
      {showModelConfig ? (
        <ModelConfigPanel />
      ) : (
        <SetupPanel
          currentPath={projectState.currentPath}
          setCurrentPath={projectState.setCurrentPath}
          historyPaths={projectState.historyPaths}
          setHistoryPaths={projectState.setHistoryPaths}
          onChooseDirectory={projectState.chooseDirectory}
          onOpenProject={projectState.openProject}
          disabled={!projectState.currentPath}
        />
      )}
      <div className="workspace">
        <ChapterTree
          tree={projectState.tree}
          project={projectState.project}
          selectedChapterId={selectedChapterId}
          selectedSceneId={sceneState.scene?.id}
          onCreateVolume={() => handleCreate('卷')}
          onCreateChapter={(vId) => handleCreate('章节', vId)}
          onCreateScene={(cId) => handleCreate('场景', cId)}
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
