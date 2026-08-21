import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import { useSSE } from './useSSE'

export function useGeneration(sceneId, onGenerated) {
  const [runs, setRuns] = useState([])
  const [activeRunId, setActiveRunId] = useState(null)
  const [streamingText, setStreamingText] = useState('')
  const [statusText, setStatusText] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  const loadRuns = useCallback(async () => {
    if (!sceneId) return
    try {
      const list = await api.listGenerationRuns(sceneId)
      setRuns(list)
      const running = list.find((r) => ['CREATED', 'PENDING', 'RUNNING'].includes(r.status))
      if (running) {
        setActiveRunId(running.id)
        setGenerating(true)
      }
    } catch (err) {
      setError(err.message)
    }
  }, [sceneId])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  const handleSSEEvent = useCallback((type, data) => {
    if (type === 'connected') {
      setStatusText(`正在调用模型: ${data.model || ''}`)
    } else if (type === 'chunk') {
      setStreamingText((prev) => prev + (data.token || ''))
    } else if (type === 'checkpoint') {
      setStatusText(data.message || '')
    } else if (type === 'success') {
      setGenerating(false)
      setActiveRunId(null)
      setStatusText('生成完成')
      loadRuns()
      if (onGenerated) onGenerated(data.final_content)
    } else if (type === 'failed') {
      setGenerating(false)
      setActiveRunId(null)
      setError(data.message || '生成失败')
      loadRuns()
    } else if (type === 'cancelled') {
      setGenerating(false)
      setActiveRunId(null)
      setStatusText('任务已取消')
      loadRuns()
    }
  }, [loadRuns, onGenerated])

  useSSE(activeRunId, handleSSEEvent)

  const startGeneration = async (params) => {
    if (!sceneId) return
    setError(null)
    setStreamingText('')
    setStatusText('任务创建中...')
    setGenerating(true)
    try {
      const res = await api.createGenerationRun(sceneId, params)
      setActiveRunId(res.id)
      await loadRuns()
      return res
    } catch (err) {
      setGenerating(false)
      setError(err.message)
      throw err
    }
  }

  const cancelGeneration = async () => {
    if (!activeRunId) return
    try {
      await api.cancelGenerationRun(activeRunId)
      setGenerating(false)
      setActiveRunId(null)
      await loadRuns()
    } catch (err) {
      setError(err.message)
    }
  }

  return {
    runs,
    generating,
    activeRunId,
    streamingText,
    statusText,
    error,
    startGeneration,
    cancelGeneration,
    loadRuns,
  }
}
