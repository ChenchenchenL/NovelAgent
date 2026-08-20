/**
 * Unified API Client for NovelAgent Frontend
 */
export async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    let msg = response.statusText
    try {
      const err = await response.json()
      msg = err.detail ? (typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)) : JSON.stringify(err)
    } catch {
      msg = await response.text()
    }
    const error = new Error(msg)
    error.status = response.status
    throw error
  }

  return response.json()
}

export const api = {
  // System
  initSession: () => request('/api/session'),
  selectDirectory: (body) => request('/api/workspaces/select-directory', { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  selectHistory: () => request('/api/workspaces/select-history', { method: 'POST' }),
  saveModelSettings: (body) => request('/api/settings/model', { method: 'POST', body: JSON.stringify(body) }),

  // Projects
  openProject: (path) => request('/api/projects/open', { method: 'POST', body: JSON.stringify({ path }) }),
  getCurrentProject: () => request('/api/projects/current'),
  getTree: () => request('/api/projects/current/tree'),
  createVolume: (title) => request('/api/projects/current/volumes', { method: 'POST', body: JSON.stringify({ title }) }),
  importHistory: (source_path) => request('/api/projects/current/import', { method: 'POST', body: JSON.stringify({ source_path }) }),

  // Chapters
  createChapter: (data) => request('/api/projects/current/chapters', { method: 'POST', body: JSON.stringify(data) }),
  getChapter: (chapterId) => request(`/api/chapters/${chapterId}`),
  updateChapterStatus: (chapterId, status) => request(`/api/chapters/${chapterId}/status`, { method: 'POST', body: JSON.stringify({ status }) }),

  // Scenes & Revisions
  createScene: (chapterId, data) => request(`/api/chapters/${chapterId}/scenes`, { method: 'POST', body: JSON.stringify(data) }),
  getScene: (sceneId) => request(`/api/scenes/${sceneId}`),
  updateSceneStatus: (sceneId, status) => request(`/api/scenes/${sceneId}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  createPatch: (sceneId, data) => request(`/api/scenes/${sceneId}/patches`, { method: 'POST', body: JSON.stringify(data) }),
  acceptRevision: (sceneId, revisionId) => request(`/api/scenes/${sceneId}/revisions/${revisionId}/accept`, { method: 'POST' }),
  getRevisions: (sceneId) => request(`/api/scenes/${sceneId}/revisions`),
  getRevision: (sceneId, revisionId) => request(`/api/scenes/${sceneId}/revisions/${revisionId}`),

  // Workspaces & TextPatches (Phase 2)
  getWorkspace: (sceneId) => request(`/api/scenes/${sceneId}/workspace`),
  updateWorkspace: (sceneId, data) => request(`/api/scenes/${sceneId}/workspace`, { method: 'PUT', body: JSON.stringify(data) }),
  snapshotWorkspace: (sceneId) => request(`/api/scenes/${sceneId}/workspace/snapshot`, { method: 'POST' }),
  restoreWorkspace: (sceneId) => request(`/api/scenes/${sceneId}/workspace/restore`, { method: 'POST' }),
  resetWorkspace: (sceneId) => request(`/api/scenes/${sceneId}/workspace`, { method: 'DELETE' }),
  applyTextPatch: (sceneId, patch) => request(`/api/scenes/${sceneId}/text-patches`, { method: 'POST', body: JSON.stringify(patch) }),
  mergePatches: (sceneId, data) => request(`/api/scenes/${sceneId}/patches/merge`, { method: 'POST', body: JSON.stringify(data) }),
  selectiveAccept: (sceneId, data) => request(`/api/scenes/${sceneId}/patches/selective-accept`, { method: 'POST', body: JSON.stringify(data) }),
  getDiff: (sceneId, revisionId, against) => request(`/api/scenes/${sceneId}/revisions/${revisionId}/diff${against ? `?against=${against}` : ''}`),
}
