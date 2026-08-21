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

  // Continuity (Phase 6)
  getCharacters: () => request('/api/characters'),
  createCharacter: (data) => request('/api/characters', { method: 'POST', body: JSON.stringify(data) }),
  getCharacter: (id) => request(`/api/characters/${id}`),
  updateCharacter: (id, data) => request(`/api/characters/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCharacter: (id) => request(`/api/characters/${id}`, { method: 'DELETE' }),
  getCharacterStates: (id) => request(`/api/characters/${id}/states`),
  createCharacterState: (id, data) => request(`/api/characters/${id}/states`, { method: 'POST', body: JSON.stringify(data) }),
  getCharacterKnowledge: (id) => request(`/api/characters/${id}/knowledge`),

  getRelationships: (charId) => request(`/api/relationships${charId ? `?character_id=${charId}` : ''}`),
  createRelationship: (data) => request('/api/relationships', { method: 'POST', body: JSON.stringify(data) }),
  getCurrentRelationships: (charId) => request(`/api/relationships/current${charId ? `?character_id=${charId}` : ''}`),

  getSecrets: () => request('/api/secrets'),
  createSecret: (data) => request('/api/secrets', { method: 'POST', body: JSON.stringify(data) }),
  getSecret: (id) => request(`/api/secrets/${id}`),
  revealSecret: (id, data) => request(`/api/secrets/${id}/reveal`, { method: 'POST', body: JSON.stringify(data) }),
  deleteSecret: (id) => request(`/api/secrets/${id}`, { method: 'DELETE' }),
  checkKnowledgeViolation: (sceneId, data) => request(`/api/scenes/${sceneId}/check-knowledge`, { method: 'POST', body: JSON.stringify(data) }),

  getItems: () => request('/api/items'),
  createItem: (data) => request('/api/items', { method: 'POST', body: JSON.stringify(data) }),
  getItem: (id) => request(`/api/items/${id}`),
  recordItemEvent: (id, data) => request(`/api/items/${id}/events`, { method: 'POST', body: JSON.stringify(data) }),
  getItemHistory: (id) => request(`/api/items/${id}/history`),

  getShadowEntities: () => request('/api/shadow-entities'),
  createShadowEntity: (data) => request('/api/shadow-entities', { method: 'POST', body: JSON.stringify(data) }),
  getShadowEntity: (id) => request(`/api/shadow-entities/${id}`),
  createIdentityHypothesis: (id, data) => request(`/api/shadow-entities/${id}/hypotheses`, { method: 'POST', body: JSON.stringify(data) }),
  revealShadowEntity: (id, data) => request(`/api/shadow-entities/${id}/reveal`, { method: 'POST', body: JSON.stringify(data) }),
  getShadowHistory: (id) => request(`/api/shadow-entities/${id}/history`),

  getLocations: () => request('/api/locations'),
  createLocation: (data) => request('/api/locations', { method: 'POST', body: JSON.stringify(data) }),
  getLocation: (id) => request(`/api/locations/${id}`),
  updateLocation: (id, data) => request(`/api/locations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteLocation: (id) => request(`/api/locations/${id}`, { method: 'DELETE' }),
  getTravelProfiles: () => request('/api/travel-profiles'),
  createTravelProfile: (data) => request('/api/travel-profiles', { method: 'POST', body: JSON.stringify(data) }),
  deleteTravelProfile: (id) => request(`/api/travel-profiles/${id}`, { method: 'DELETE' }),
  getMovements: () => request('/api/movements'),
  createMovement: (data) => request('/api/movements', { method: 'POST', body: JSON.stringify(data) }),
  checkMovementFeasibility: (sceneId, data) => request(`/api/scenes/${sceneId}/check-movement`, { method: 'POST', body: JSON.stringify(data) }),

  // Stage 7: Plot, Foreshadowing, Transition, Impact Graph
  getPlotThreads: () => request('/api/plot-threads'),
  createPlotThread: (data) => request('/api/plot-threads', { method: 'POST', body: JSON.stringify(data) }),
  getPlotThread: (id) => request(`/api/plot-threads/${id}`),
  updatePlotThread: (id, data) => request(`/api/plot-threads/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlotThread: (id) => request(`/api/plot-threads/${id}`, { method: 'DELETE' }),
  getPlotThreadEvents: (id) => request(`/api/plot-threads/${id}/events`),
  createPlotEvent: (id, data) => request(`/api/plot-threads/${id}/events`, { method: 'POST', body: JSON.stringify(data) }),

  getForeshadowings: (status, threadId) => {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (threadId) params.append('plot_thread_id', threadId)
    const qs = params.toString()
    return request(`/api/foreshadowings${qs ? `?${qs}` : ''}`)
  },
  createForeshadowing: (data) => request('/api/foreshadowings', { method: 'POST', body: JSON.stringify(data) }),
  payoffForeshadowing: (id, data) => request(`/api/foreshadowings/${id}/payoff`, { method: 'POST', body: JSON.stringify(data) }),
  deleteForeshadowing: (id) => request(`/api/foreshadowings/${id}`, { method: 'DELETE' }),
  getScheduledForeshadowings: (sceneId) => request(`/api/scenes/${sceneId}/foreshadowings/scheduled`),

  checkSceneTransition: (sceneId, data = {}) => request(`/api/scenes/${sceneId}/check-transition`, { method: 'POST', body: JSON.stringify(data) }),
  getSceneTransitionReport: (sceneId) => request(`/api/scenes/${sceneId}/transition-report`),
  updateSceneContracts: (sceneId, data) => request(`/api/scenes/${sceneId}/contracts`, { method: 'PUT', body: JSON.stringify(data) }),

  getImpactNodes: (sceneId) => request(`/api/impact-graph/nodes${sceneId ? `?scene_id=${sceneId}` : ''}`),
  createImpactNode: (data) => request('/api/impact-graph/nodes', { method: 'POST', body: JSON.stringify(data) }),
  getImpactEdges: () => request('/api/impact-graph/edges'),
  createImpactEdge: (data) => request('/api/impact-graph/edges', { method: 'POST', body: JSON.stringify(data) }),
  propagateImpact: (data) => request('/api/impact-graph/propagate', { method: 'POST', body: JSON.stringify(data) }),
  getSceneImpactReport: (sceneId) => request(`/api/scenes/${sceneId}/impact-report`),
  getProjectImpactSummary: () => request('/api/projects/current/impact-summary'),
}

