import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

export function useModelConfig() {
  const [config, setConfig] = useState({ endpoint: '', models: {}, has_key: false })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [testResult, setTestResult] = useState(null)

  const fetchConfig = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getModelConfig()
      setConfig(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  const saveConfig = async ({ endpoint, models, apiKey }) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.updateModelConfig({ endpoint, models, api_key: apiKey || undefined })
      setConfig((prev) => ({ ...prev, ...res, has_key: res.key_saved }))
      return res
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async (payload) => {
    setLoading(true)
    setError(null)
    setTestResult(null)
    try {
      const res = await api.testModelConnection(payload)
      setTestResult(res)
      return res
    } catch (err) {
      const errRes = { status: 'error', error: err.message }
      setTestResult(errRes)
      return errRes
    } finally {
      setLoading(false)
    }
  }

  const removeApiKey = async () => {
    try {
      await api.deleteApiKey()
      setConfig((prev) => ({ ...prev, has_key: false }))
    } catch (err) {
      setError(err.message)
    }
  }

  return { config, loading, error, testResult, saveConfig, testConnection, removeApiKey, refetch: fetchConfig }
}
