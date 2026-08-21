import React, { useEffect, useState } from 'react'

export function EvidenceViewer({ candidate, onSaveDecision, onCancel }) {
  const [subject, setSubject] = useState('')
  const [predicate, setPredicate] = useState('')
  const [objectValue, setObjectValue] = useState('')
  const [modality, setModality] = useState('ACTUAL')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (candidate) {
      setSubject(candidate.subject || '')
      setPredicate(candidate.predicate || '')
      setObjectValue(candidate.object_value || '')
      setModality(candidate.modality || 'ACTUAL')
      setNotes('')
    }
  }, [candidate])

  if (!candidate) {
    return (
      <div className="evidence-empty-panel">
        <p>👈 请从左侧候选列表中选择一项事实主张，查看原文证据与进行仲裁修正</p>
      </div>
    )
  }

  const handleConfirm = () => {
    onSaveDecision(candidate.id, 'CONFIRM', {
      subject,
      predicate,
      object_value: objectValue,
      modality,
    }, notes)
  }

  return (
    <div className="evidence-viewer-box">
      <div className="evidence-header">
        <h4>原文证据与主张审查 #{candidate.id}</h4>
        <span className="offsets-info">字符偏移: [{candidate.source_start} ~ {candidate.source_end}]</span>
      </div>

      <div className="evidence-quote">
        <label>原文段落证据：</label>
        <blockquote>{candidate.source_text}</blockquote>
      </div>

      <div className="evidence-form">
        <div className="form-row">
          <div className="form-group">
            <label>主体 (Subject)</label>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
          <div className="form-group">
            <label>谓词 (Predicate)</label>
            <input value={predicate} onChange={(e) => setPredicate(e.target.value)} />
          </div>
          <div className="form-group">
            <label>客体 (Object)</label>
            <input value={objectValue} onChange={(e) => setObjectValue(e.target.value)} />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>事实模态 (Modality)</label>
            <select value={modality} onChange={(e) => setModality(e.target.value)}>
              <option value="ACTUAL">ACTUAL - 真实发生（参与硬规则）</option>
              <option value="BELIEVED">BELIEVED - 角色相信</option>
              <option value="REPORTED">REPORTED - 传言转述</option>
              <option value="REMEMBERED">REMEMBERED - 回忆</option>
              <option value="DREAMED">DREAMED - 梦境幻觉</option>
              <option value="HYPOTHETICAL">HYPOTHETICAL - 假设推断</option>
              <option value="COUNTERFACTUAL">COUNTERFACTUAL - 反事实</option>
              <option value="METAPHORICAL">METAPHORICAL - 隐喻比喻</option>
              <option value="AMBIGUOUS">AMBIGUOUS - 存疑待定</option>
            </select>
          </div>
          <div className="form-group">
            <label>作者仲裁备注 (Notes)</label>
            <input value={notes} placeholder="可选填写仲裁依据..." onChange={(e) => setNotes(e.target.value)} />
          </div>
        </div>

        <div className="evidence-actions">
          <button className="btn-secondary" onClick={onCancel}>取消选择</button>
          <button className="btn-primary" onClick={handleConfirm}>✓ 修正并采纳为正典</button>
        </div>
      </div>
    </div>
  )
}
