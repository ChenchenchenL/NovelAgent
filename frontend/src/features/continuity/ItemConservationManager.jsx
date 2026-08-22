import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ItemConservationManager({ currentSceneId }) {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [holder, setHolder] = useState('')
  const [transferTarget, setTransferTarget] = useState('')
  const [selectedItemId, setSelectedItemId] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadItems = async () => {
    try { setItems((await api.getItems()) || []) } catch (e) { console.error(e) }
  }

  useEffect(() => { loadItems() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createItem({ name: name.trim(), unique_item: true, current_holder: holder.trim() || null, current_state: holder.trim() ? 'HELD' : 'CREATED' })
      setName(''); setHolder(''); await loadItems()
    } finally { setLoading(false) }
  }

  const handleTransfer = async (item) => {
    if (!transferTarget.trim()) return
    try {
      await api.recordItemEvent(item.id, { event_type: 'TRANSFERRED', from_holder: item.current_holder, to_holder: transferTarget.trim(), scene_id: currentSceneId || 1 })
      setTransferTarget(''); setSelectedItemId(null); await loadItems()
    } catch (err) { alert(err.message || '流转失败') }
  }

  return (
    <div className="continuity-subpanel">
      <form onSubmit={handleCreate} className="continuity-form-card">
        <span style={{ fontSize: '13px', fontWeight: 650, color: '#09090b' }}>登记核心道具与线索物</span>
        <div className="continuity-form-row">
          <input placeholder="道具名称 * (例如: 废弃金丹芯片)" value={name} onChange={e => setName(e.target.value)} required />
          <input placeholder="初始持有者姓名 (例如: 林舟)" value={holder} onChange={e => setHolder(e.target.value)} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={loading} className="btn-blue">登记道具</button>
        </div>
      </form>

      <div className="continuity-cards-grid">
        {items.map(item => (
          <div key={item.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong style={{ fontSize: '13.5px', color: '#09090b' }}>{item.name}</strong>
              <span className="badge blue">当前持有：{item.current_holder || '未分配'}</span>
            </div>
            <div style={{ marginTop: '6px' }}>
              {selectedItemId === item.id ? (
                <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                  <input placeholder="移交给谁？" value={transferTarget} onChange={e => setTransferTarget(e.target.value)} style={{ flex: 1 }} />
                  <button onClick={() => handleTransfer(item)} className="btn-small btn-blue">确认</button>
                  <button onClick={() => setSelectedItemId(null)} className="btn-small">取消</button>
                </div>
              ) : (
                <button onClick={() => { setSelectedItemId(item.id); setTransferTarget('') }} className="mini-btn">流转道具</button>
              )}
            </div>
          </div>
        ))}
      </div>
      {items.length === 0 && <div className="empty-state">暂无关键道具记录</div>}
    </div>
  )
}
