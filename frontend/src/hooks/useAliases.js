import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

export function useAliases() {
  const [aliases, setAliases] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadAliases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getEntityAliases()
      setAliases(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAliases()
  }, [loadAliases])

  const addAlias = async (canonicalName, aliasName, aliasType = 'informal') => {
    setLoading(true)
    try {
      const res = await api.createEntityAlias({
        canonical_name: canonicalName,
        alias_name: aliasName,
        alias_type: aliasType,
      })
      await loadAliases()
      return res
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const removeAlias = async (aliasId) => {
    try {
      await api.deleteEntityAlias(aliasId)
      await loadAliases()
    } catch (err) {
      setError(err.message)
    }
  }

  return { aliases, loading, error, addAlias, removeAlias, reload: loadAliases }
}
