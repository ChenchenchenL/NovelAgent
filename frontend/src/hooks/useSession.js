import { useEffect } from 'react'
import { api } from '../api/client'

export function useSession(setNotice) {
  useEffect(() => {
    api.initSession().catch((err) => setNotice(err.message))
  }, [setNotice])
}
