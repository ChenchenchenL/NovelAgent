import { useEffect, useRef, useState } from 'react'

export function useSSE(runId, onEvent) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const lastSeqRef = useRef(0)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    if (!runId) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      setIsConnected(false)
      return
    }

    let isSubscribed = true
    const url = `/api/generation-runs/${runId}/sse?since=${lastSeqRef.current}`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      if (isSubscribed) setIsConnected(true)
    }

    const eventTypes = ['connected', 'chunk', 'checkpoint', 'extraction_candidate', 'success', 'failed', 'cancelled']
    eventTypes.forEach((type) => {
      es.addEventListener(type, (evt) => {
        if (!isSubscribed) return
        if (evt.lastEventId) {
          lastSeqRef.current = parseInt(evt.lastEventId, 10) || lastSeqRef.current
        }
        try {
          const data = JSON.parse(evt.data)
          if (onEvent) onEvent(type, data)
        } catch {
          if (onEvent) onEvent(type, evt.data)
        }

        if (['success', 'failed', 'cancelled'].includes(type)) {
          es.close()
          setIsConnected(false)
        }
      })
    })

    es.onerror = () => {
      if (isSubscribed) {
        setError('SSE 连接中断')
        setIsConnected(false)
      }
    }

    return () => {
      isSubscribed = false
      es.close()
    }
  }, [runId, onEvent])

  return { isConnected, error }
}
