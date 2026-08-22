import React, { useState, useEffect } from 'react'
import { api } from '../../api/client'

export function ItemConservationManager({ currentSceneId }) {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [holder, setHolder] = useState('')
  const [uniqueItem, setUniqueItem] = useState(true)
  const [transferTarget, setTransferTarget] = useState('')
  const [selectedItemId, setSelectedItemId] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const loadItems = async () => {
    try {
      const res = await api.getItems()
      setItems(res)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { loadItems() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.createItem({ name, unique_item: uniqueItem, current_holder: holder || null, current_state: holder ? 'HELD' : 'CREATED' })
      setName('')
      setHolder('')
      await loadItems()
    } finally {
      setLoading(false)
    }
  }

  const handleTransfer = async (item) => {
    if (!transferTarget.trim()) return
    setErrorMsg('')
    try {
      await api.recordItemEvent(item.id, {
        event_type: 'TRANSFERRED',
        from_holder: item.current_holder,
        to_holder: transferTarget.trim(),
        scene_id: currentSceneId || 1,
      })
      setTransferTarget('')
      setSelectedItemId(null)
      await loadItems()
    } catch (err) {
      setErrorMsg(err.message || '流转失败')
    }
  }

  return (
    <div className="continuity-subpanel">
      {errorMsg && <div className="error-banner">{errorMsg}</div>}
      <form onSubmit={handleCreate} className="continuity-form">
        <input placeholder="物品名称 *" value={name} onChange={e => setName(e.target.value)} required />
        <input placeholder="初始持有者" value={holder} onChange={e => setHolder(e.target.value)} />
        <label className="checkbox-label">
          <input type="checkbox" checked={uniqueItem} onChange={e => setUniqueItem(e.target.checked)} /> 唯一物品 (严格守恒)
        </label>
        <button type="submit" disabled={loading} className="btn-primary">创建物品</button>
      </form>
      <div className="continuity-list">
        {items.map(item => (
          <div key={item.id} className="continuity-card">
            <div className="continuity-card-header">
              <strong>{item.name}</strong>
              <span className={`badge ${item.current_state === 'DESTROYED' ? 'danger' : 'info'}`}>{item.current_state}</span>
            </div>
            <div className="card-desc">持有者: <strong>{item.current_holder || '无 (未被持有)'}</strong> {item.unique_item && '· 唯一专属'}</div>
            {item.current_state !== 'DESTROYED' && (
              <div className="action-row">
                {selectedItemId === item.id ? (
                  <>
                    <input placeholder="接收人" value={transferTarget} onChange={e => setTransferTarget(e.target.value)} />
                    <button onClick={() => handleTransfer(item)} className="btn-sm btn-primary">确认流转</button>
                    <button onClick={() => setSelectedItemId(null)} className="btn-sm">取消</button>
                  </>
                ) : (
                  <button onClick={() => { setSelectedItemId(item.id); setTransferTarget('') }} className="btn-sm">流转物品</button>
                )}
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && <div className="empty-state">暂无物品记录</div>}
      </div>
    </div>
  )
}
