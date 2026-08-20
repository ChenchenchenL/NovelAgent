import { useState } from 'react'
import { api } from '../api/client'

export function useScene(setNotice, refreshTree) {
  const [scene, setScene] = useState(null)
  const [revisions, setRevisions] = useState([])
  const [viewingRevision, setViewingRevision] = useState(null)
  const [busy, setBusy] = useState(false)

  const selectScene = async (sceneId) => {
    try {
      const loaded = await api.getScene(sceneId)
      setScene(loaded)
      setViewingRevision(null)
      const revs = await api.getRevisions(sceneId)
      setRevisions(revs)
      setNotice(`已加载场景：${loaded.title}`)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const saveScene = async () => {
    if (!scene) return
    setBusy(true)
    try {
      const revision = await api.createPatch(scene.id, {
        base_revision_id: scene.current_revision_id,
        content: scene.content,
        source: 'AUTHOR',
      })
      await api.acceptRevision(scene.id, revision.revision_id)
      const loaded = await api.getScene(scene.id)
      setScene(loaded)
      const revs = await api.getRevisions(scene.id)
      setRevisions(revs)
      await refreshTree()
      setNotice('场景不可变版本已提交至正典与文件')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setBusy(false)
    }
  }

  const changeSceneStatus = async (sceneId, status) => {
    try {
      await api.updateSceneStatus(sceneId, status)
      const loaded = await api.getScene(sceneId)
      setScene(loaded)
      await refreshTree()
      setNotice(`场景状态已变更为：${status}`)
    } catch (err) {
      setNotice(`场景状态变更失败：${err.message}`)
    }
  }

  const viewRevision = async (revId) => {
    if (!scene) return
    try {
      const rev = await api.getRevision(scene.id, revId)
      setViewingRevision(rev)
      setNotice(`正在预览历史版本 #${rev.id}`)
    } catch (err) {
      setNotice(err.message)
    }
  }

  return {
    scene,
    setScene,
    revisions,
    viewingRevision,
    setViewingRevision,
    busy,
    selectScene,
    saveScene,
    changeSceneStatus,
    viewRevision,
  }
}
