import { useState } from 'react'
import { api } from '../api/client'

export function useProject(setNotice) {
  const [project, setProject] = useState(null)
  const [tree, setTree] = useState({ volumes: [], unassigned_chapters: [] })
  const [currentPath, setCurrentPath] = useState('')
  const [historyPaths, setHistoryPaths] = useState('')

  const refreshTree = async () => {
    try {
      const data = await api.getTree()
      setTree(data)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const openProject = async () => {
    try {
      const opened = await api.openProject(currentPath)
      setProject(opened)
      await refreshTree()
      setNotice(`已打开项目：${opened.name}`)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const chooseDirectory = async () => {
    try {
      const body = currentPath
        ? {
            current_path: currentPath,
            history_paths: historyPaths.split('\n').map((s) => s.trim()).filter(Boolean),
          }
        : undefined
      const selected = await api.selectDirectory(body)
      setCurrentPath(selected.current_path)
      setNotice(`已授权目录：${selected.current_path}`)
    } catch (err) {
      setNotice(err.message)
    }
  }

  return {
    project,
    tree,
    currentPath,
    setCurrentPath,
    historyPaths,
    setHistoryPaths,
    refreshTree,
    openProject,
    chooseDirectory,
  }
}
