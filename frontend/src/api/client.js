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
  // System & Recovery (Phase 0 & Phase 5)
  initSession: () => request('/api/session'),
  selectDirectory: (body) => request('/api/workspaces/select-directory', { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  selectHistory: () => request('/api/workspaces/select-history', { method: 'POST' }),
  saveModelSettings: (body) => request('/api/settings/model', { method: 'POST', body: JSON.stringify(body) }),
  runFsck: () => request('/api/projects/current/fsck', { method: 'POST' }),
  runFsckFix: () => request('/api/projects/current/fsck/fix', { method: 'POST' }),
  resolveFsckConflict: (data) => request('/api/projects/current/fsck/resolve-conflict', { method: 'POST', body: JSON.stringify(data) }),
  backupProject: (data) => request('/api/projects/current/backup', { method: 'POST', body: JSON.stringify(data || {}) }),
  exportProject: (data) => request('/api/projects/current/export', { method: 'POST', body: JSON.stringify(data) }),
  restoreProject: (data) => request('/api/projects/current/restore', { method: 'POST', body: JSON.stringify(data) }),

  // Projects
  openProject: (path) => request('/api/projects/open', { method: 'POST', body: JSON.stringify({ path }) }),
  getCurrentProject: () => request('/api/projects/current'),
  getTree: () => request('/api/projects/current/tree'),
  createVolume: (title) => request('/api/projects/current/volumes', { method: 'POST', body: JSON.stringify({ title }) }),
  importHistory: (source_path) => request('/api/projects/current/import', { method: 'POST', body: JSON.stringify({ source_path }) }),

  // Import Jobs (Phase 5)
  createImportJob: (data) => request('/api/projects/current/import-jobs', { method: 'POST', body: JSON.stringify(data) }),
  listImportJobs: () => request('/api/import-jobs'),
  getImportJob: (jobId) => request(`/api/import-jobs/${jobId}`),
  pauseImportJob: (jobId) => request(`/api/import-jobs/${jobId}/pause`, { method: 'POST' }),
  resumeImportJob: (jobId) => request(`/api/import-jobs/${jobId}/resume`, { method: 'POST' }),
  retryImportJob: (jobId) => request(`/api/import-jobs/${jobId}/retry`, { method: 'POST' }),
  cancelImportJob: (jobId) => request(`/api/import-jobs/${jobId}`, { method: 'DELETE' }),
  getImportCheckpoints: (jobId) => request(`/api/import-jobs/${jobId}/checkpoints`),

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

  // Model & Generation (Phase 3)
  getModelConfig: () => request('/api/model/config'),
  updateModelConfig: (data) => request('/api/model/config', { method: 'PUT', body: JSON.stringify(data) }),
  testModelConnection: (data) => request('/api/model/test', { method: 'POST', body: JSON.stringify(data || {}) }),
  deleteApiKey: () => request('/api/model/api-key', { method: 'DELETE' }),
  createGenerationRun: (sceneId, data) => request(`/api/scenes/${sceneId}/generation-runs`, { method: 'POST', body: JSON.stringify(data) }),
  getGenerationRun: (runId) => request(`/api/generation-runs/${runId}`),
  cancelGenerationRun: (runId) => request(`/api/generation-runs/${runId}/cancel`, { method: 'POST' }),
  listGenerationRuns: (sceneId) => request(`/api/generation-runs${sceneId ? `?scene_id=${sceneId}` : ''}`),

  // Claims & Extraction & Arbitration (Phase 4)
  extractSceneClaims: (sceneId, data) => request(`/api/scenes/${sceneId}/extract`, { method: 'POST', body: JSON.stringify(data || {}) }),
  batchExtractChapter: (chapterId, data) => request(`/api/chapters/${chapterId}/batch-extract`, { method: 'POST', body: JSON.stringify(data || {}) }),
  getClaimCandidates: (sceneId, status) => request(`/api/scenes/${sceneId}/claim-candidates${status ? `?status=${status}` : ''}`),
  getCanonClaims: (sceneId) => request(`/api/scenes/${sceneId}/canon-claims`),
  decideClaimCandidate: (candidateId, data) => request(`/api/claim-candidates/${candidateId}/decision`, { method: 'POST', body: JSON.stringify(data) }),
  batchDecideClaimCandidates: (sceneId, data) => request(`/api/scenes/${sceneId}/claim-candidates/batch-decision`, { method: 'POST', body: JSON.stringify(data) }),
  getClaimConflicts: (sceneId) => request(`/api/claims/conflicts${sceneId ? `?scene_id=${sceneId}` : ''}`),
  getEntityAliases: () => request('/api/entity-aliases'),
  createEntityAlias: (data) => request('/api/entity-aliases', { method: 'POST', body: JSON.stringify(data) }),
  deleteEntityAlias: (aliasId) => request(`/api/entity-aliases/${aliasId}`, { method: 'DELETE' }),
}
