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

  // Stage 8: Search, Vector, KG, H-RAG, ContextPack & Index Management
  searchFts: (params) => {
    const q = new URLSearchParams(params).toString()
    return request(`/api/search/fts?${q}`)
  },
  searchVector: (params) => {
    const q = new URLSearchParams(params).toString()
    return request(`/api/search/vector?${q}`)
  },
  searchHrag: (sceneId, maxTokens = 4000) => request(`/api/search/hrag?scene_id=${sceneId}&max_tokens=${maxTokens}`),

  getKgNodes: (nodeType) => request(`/api/kg/nodes${nodeType ? `?node_type=${nodeType}` : ''}`),
  getKgEdges: (edgeType) => request(`/api/kg/edges${edgeType ? `?edge_type=${edgeType}` : ''}`),
  queryKgPath: (data) => request('/api/kg/path', { method: 'POST', body: JSON.stringify(data) }),
  queryKgNeighbors: (nodeId) => request(`/api/kg/neighbors?node_id=${nodeId}`),

  getSummaries: (type) => request(`/api/summaries${type ? `?summary_type=${type}` : ''}`),
  createSummary: (data) => request('/api/summaries', { method: 'POST', body: JSON.stringify(data) }),
  rebuildSummaries: () => request('/api/summaries/rebuild', { method: 'POST' }),

  assembleContextPack: (data) => request('/api/context-packs', { method: 'POST', body: JSON.stringify(data) }),
  validateContextPack: (data) => request('/api/context-packs/validate', { method: 'POST', body: JSON.stringify(data) }),

  getIndexesStatus: () => request('/api/indexes/status'),
  rebuildAllIndexes: () => request('/api/indexes/rebuild-all', { method: 'POST' }),
  rebuildFtsIndex: () => request('/api/indexes/fts/rebuild', { method: 'POST' }),
  rebuildVectorIndex: () => request('/api/indexes/vector/rebuild', { method: 'POST' }),
  rebuildKgIndex: () => request('/api/indexes/kg/rebuild', { method: 'POST' }),
  validateIndexes: () => request('/api/indexes/validate', { method: 'POST' }),

  // Stage 9: Quality Control, Beat Contracts, Cliche Blacklist, Voice Fingerprints & Feedback
  getSceneBeats: (sceneId) => request(`/api/scenes/${sceneId}/beats`),
  createSceneBeat: (sceneId, data) => request(`/api/scenes/${sceneId}/beats`, { method: 'POST', body: JSON.stringify(data) }),
  getBeat: (id) => request(`/api/beats/${id}`),
  updateBeat: (id, data) => request(`/api/beats/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  advanceBeat: (id, data) => request(`/api/beats/${id}/advance`, { method: 'POST', body: JSON.stringify(data) }),
  stopBeat: (id, data) => request(`/api/beats/${id}/stop`, { method: 'POST', body: JSON.stringify(data) }),

  getClicheBlacklist: (params) => {
    const q = new URLSearchParams(params || {}).toString()
    return request(`/api/cliche-blacklist${q ? `?${q}` : ''}`)
  },
  createClicheEntry: (data) => request('/api/cliche-blacklist', { method: 'POST', body: JSON.stringify(data) }),
  updateClicheEntry: (id, data) => request(`/api/cliche-blacklist/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteClicheEntry: (id) => request(`/api/cliche-blacklist/${id}`, { method: 'DELETE' }),
  scanCliches: (data) => request('/api/cliche-blacklist/scan', { method: 'POST', body: JSON.stringify(data) }),

  getVoiceFingerprint: (characterId) => request(`/api/characters/${characterId}/voice-fingerprint`),
  setVoiceFingerprint: (characterId, data) => request(`/api/characters/${characterId}/voice-fingerprint`, { method: 'POST', body: JSON.stringify(data) }),
  extractVoiceFingerprint: (characterId) => request(`/api/characters/${characterId}/voice-fingerprint/extract`, { method: 'POST' }),
  checkVoiceDrift: (data) => request('/api/voice-drift-check', { method: 'POST', body: JSON.stringify(data) }),
  getVoiceLexicons: (characterId) => request(`/api/voice-lexicons${characterId ? `?character_id=${characterId}` : ''}`),
  createVoiceLexicon: (data) => request('/api/voice-lexicons', { method: 'POST', body: JSON.stringify(data) }),
  deleteVoiceLexicon: (id) => request(`/api/voice-lexicons/${id}`, { method: 'DELETE' }),

  checkSceneQuality: (sceneId, data = {}) => request(`/api/scenes/${sceneId}/quality-check`, { method: 'POST', body: JSON.stringify(data) }),
  getSceneQualityReport: (sceneId) => request(`/api/scenes/${sceneId}/quality-report`),
  getProjectQualityReports: () => request('/api/quality-reports'),

  getAuthorFeedback: (params) => {
    const q = new URLSearchParams(params || {}).toString()
    return request(`/api/author-feedback${q ? `?${q}` : ''}`)
  },
  createAuthorFeedback: (data) => request('/api/author-feedback', { method: 'POST', body: JSON.stringify(data) }),
  getAuthorFeedbackStats: () => request('/api/author-feedback/stats'),

  // Stage 10: Communities, GraphRAG, Global Analysis, Model Stats & Optimization
  getCommunities: (communityType) => request(`/api/communities${communityType ? `?community_type=${communityType}` : ''}`),
  createCommunity: (data) => request('/api/communities', { method: 'POST', body: JSON.stringify(data) }),
  autoDetectCommunities: () => request('/api/communities/auto-detect', { method: 'POST' }),
  getCommunity: (id) => request(`/api/communities/${id}`),
  updateCommunity: (id, data) => request(`/api/communities/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCommunity: (id) => request(`/api/communities/${id}`, { method: 'DELETE' }),
  getCommunitySummaries: (id) => request(`/api/communities/${id}/summaries`),
  generateCommunitySummary: (id, type = 'OVERVIEW') => request(`/api/communities/${id}/summaries/generate?summary_type=${type}`, { method: 'POST' }),

  queryGraphrag: (data) => request('/api/graphrag/query', { method: 'POST', body: JSON.stringify(data) }),
  getGraphragQueries: (type) => request(`/api/graphrag/queries${type ? `?query_type=${type}` : ''}`),
  getGraphragQuery: (id) => request(`/api/graphrag/queries/${id}`),
  retryGraphragQuery: (id) => request(`/api/graphrag/queries/${id}/retry`, { method: 'POST' }),

  runCharacterArcsAnalysis: () => request('/api/global-analysis/character-arcs', { method: 'POST' }),
  runRelationshipNetworkAnalysis: () => request('/api/global-analysis/relationship-network', { method: 'POST' }),
  runForeshadowAudit: () => request('/api/global-analysis/foreshadow-audit', { method: 'POST' }),
  runPlotRuptureAudit: () => request('/api/global-analysis/plot-rupture', { method: 'POST' }),
  getGlobalAnalysisReports: (type) => request(`/api/global-analysis/reports${type ? `?report_type=${type}` : ''}`),
  getGlobalAnalysisReport: (id) => request(`/api/global-analysis/reports/${id}`),

  getModelStatsSummary: () => request('/api/model-stats/summary'),
  getModelStatsDaily: () => request('/api/model-stats/daily'),
  getModelStatsByModel: () => request('/api/model-stats/by-model'),
  getModelStatsByTask: () => request('/api/model-stats/by-task'),
  getModelStatsDegradation: () => request('/api/model-stats/degradation'),
  aggregateModelStats: () => request('/api/model-stats/aggregate', { method: 'POST' }),

  getFeedbackOptimizationStats: () => request('/api/feedback-optimization/stats'),
  getFeedbackOptimizationSuggestions: () => request('/api/feedback-optimization/suggestions'),
  applyFeedbackOptimization: (data) => request('/api/feedback-optimization/apply', { method: 'POST', body: JSON.stringify(data) }),
}

