import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function VoiceFingerprintPanel() {
  const [characters, setCharacters] = useState([])
  const [selectedCharId, setSelectedCharId] = useState('')
  const [fingerprint, setFingerprint] = useState(null)
  const [driftText, setDriftText] = useState('')
  const [driftReport, setDriftReport] = useState([])
  const [loading, setLoading] = useState(false)

  const loadChars = async () => {
    try {
      const res = await api.getCharacters()
      setCharacters(res || [])
      if (res && res.length > 0 && !selectedCharId) {
        setSelectedCharId(res[0].id)
      }
    } catch (e) { console.error(e) }
  }

  const loadFp = async (cid) => {
    if (!cid) return
    try {
      const fp = await api.getVoiceFingerprint(cid)
      setFingerprint(fp)
    } catch { setFingerprint(null) }
  }

  useEffect(() => { loadChars() }, [])
  useEffect(() => { if (selectedCharId) loadFp(selectedCharId) }, [selectedCharId])

  const handleExtract = async () => {
    if (!selectedCharId) return
    setLoading(true)
    try {
      const res = await api.extractVoiceFingerprint(selectedCharId)
      setFingerprint(res)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleCheckDrift = async () => {
    if (!selectedCharId || !driftText.trim()) return
    try {
      const res = await api.checkVoiceDrift({ character_id: Number(selectedCharId), text: driftText.trim() })
      setDriftReport(res || [])
    } catch (e) { console.error(e) }
  }

  return (
    <div className="continuity-subpanel">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
        <select value={selectedCharId} onChange={(e) => setSelectedCharId(e.target.value)} style={{ flex: 1 }}>
          <option value="">选择人物...</option>
          {characters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn-primary" onClick={handleExtract} disabled={loading || !selectedCharId}>
          {loading ? '提取中...' : '🧬 从正典提取指纹'}
        </button>
      </div>

      {fingerprint ? (
        <div className="continuity-card" style={{ marginBottom: '16px' }}>
          <div className="continuity-card-header">
            <strong>声音指纹统计 (v{fingerprint.version}, 样本数: {fingerprint.source_text_sample_count})</strong>
            <span className="badge success">敬语等级: {fingerprint.honorific_level}</span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', display: 'flex', gap: '16px' }}>
            <span>平均句长: <strong>{fingerprint.avg_sentence_length} 字 (±{fingerprint.sentence_length_std})</strong></span>
            <span>口语率: <strong>{fingerprint.colloquial_ratio}%</strong></span>
            <span>文白率: <strong>{fingerprint.classical_ratio}%</strong></span>
          </div>
        </div>
      ) : (
        <div className="empty-state" style={{ marginBottom: '16px' }}>该人物尚未建立声音指纹模型，请点击右上角从正典提取</div>
      )}

      <h4>声音漂移与同质化检测</h4>
      <div style={{ display: 'flex', gap: '8px', marginTop: '8px', marginBottom: '12px' }}>
        <input
          type="text"
          placeholder="输入该人物的台词或动作描写文本..."
          value={driftText}
          onChange={(e) => setDriftText(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn-small" onClick={handleCheckDrift}>检测漂移</button>
      </div>

      {driftReport.length > 0 && (
        <div className="continuity-list">
          {driftReport.map((d, i) => (
            <div key={i} className="continuity-card">
              <span className="badge warning">{d.severity}</span> {d.description}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
