import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

export function useExtraction(sceneId) {
  const [candidates, setCandidates] = useState([])
  const [canonClaims, setCanonClaims] = useState([])
  const [conflicts, setConflicts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadData = useCallback(async () => {
    if (!sceneId) {
      setCandidates([])
      setCanonClaims([])
      setConflicts([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const [cands, canons, confs] = await Promise.all([
        api.getClaimCandidates(sceneId),
        api.getCanonClaims(sceneId),
        api.getClaimConflicts(sceneId),
      ])
      setCandidates(cands)
      setCanonClaims(canons)
      setConflicts(confs.conflicts || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [sceneId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const runExtraction = async (forceFullScan = false) => {
    if (!sceneId) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.extractSceneClaims(sceneId, { force_full_scan: forceFullScan })
      await loadData()
      return res
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const decide = async (candidateId, decision, corrections = null, notes = null) => {
    try {
      const res = await api.decideClaimCandidate(candidateId, { decision, corrections, notes })
      await loadData()
      return res
    } catch (err) {
      setError(err.message)
      throw err
    }
  }

  const batchDecide = async (decisions) => {
    if (!sceneId) return
    try {
      const res = await api.batchDecideClaimCandidates(sceneId, { decisions })
      await loadData()
      return res
    } catch (err) {
      setError(err.message)
      throw err
    }
  }

  return {
    candidates,
    canonClaims,
    conflicts,
    loading,
    error,
    runExtraction,
    decide,
    batchDecide,
    reload: loadData,
  }
}
