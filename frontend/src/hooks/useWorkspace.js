import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

export function useWorkspace(sceneId, initialContent = '', onError = null) {
  const [draftContent, setDraftContent] = useState(initialContent)
  const [workspace, setWorkspace] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [hasSnapshot, setHasSnapshot] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!sceneId) return
    api.getWorkspace(sceneId)
      .then((ws) => {
        setWorkspace(ws)
        setDraftContent(ws.draft_content || initialContent)
        setHasSnapshot(Boolean(ws.auto_save_snapshot))
        setSaveError(null)
      })
      .catch((err) => {
        setDraftContent(initialContent)
        if (onError) onError(err)
      })
  }, [sceneId, initialContent])

  const saveWorkspace = async (content, cursor = 0) => {
    if (!sceneId) return
    setIsSaving(true)
    try {
      const updated = await api.updateWorkspace(sceneId, {
        draft_content: content,
        cursor_position: cursor,
      })
      setWorkspace(updated)
      setSaveError(null)
    } catch (err) {
      setSaveError(err.message)
      if (onError) onError(err)
    } finally {
      setIsSaving(false)
    }
  }

  const onDraftChange = (newContent, cursor = 0) => {
    setDraftContent(newContent)
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      saveWorkspace(newContent, cursor)
    }, 2000)
  }

  const takeSnapshot = async () => {
    if (!sceneId) return
    const res = await api.snapshotWorkspace(sceneId)
    setWorkspace(res)
    setHasSnapshot(true)
  }

  const restoreSnapshot = async () => {
    if (!sceneId) return
    const res = await api.restoreWorkspace(sceneId)
    setWorkspace(res)
    setDraftContent(res.draft_content)
  }

  const resetWorkspace = async () => {
    if (!sceneId) return
    const res = await api.resetWorkspace(sceneId)
    setWorkspace(res)
    setDraftContent(res.draft_content)
    setSaveError(null)
  }

  return {
    draftContent,
    setDraftContent,
    workspace,
    isSaving,
    saveError,
    hasSnapshot,
    onDraftChange,
    saveWorkspace,
    takeSnapshot,
    restoreSnapshot,
    resetWorkspace,
  }
}
