import React, { useState } from 'react'
import { api } from '../../api/client'

export function AutoPlanModal({ isOpen, onClose, onPlanCompleted }) {
  const [seedPrompt, setSeedPrompt] = useState('底层维修工林舟在废弃金丹芯片中发现了万仙宗的灭门真相')
  const [genre, setGenre] = useState('东方玄幻/赛博仙侠')
  const [volumes, setVolumes] = useState(2)
  const [chapters, setChapters] = useState(3)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  if (!isOpen) return null

  const handlePlan = async (e) => {
    e.preventDefault()
    if (!seedPrompt.trim()) return
    setLoading(true)
    try {
      const res = await api.autoPlanNovel({
        seed_prompt: seedPrompt.trim(),
        genre,
        target_volumes: Number(volumes),
        chapters_per_vol: Number(chapters),
      })
      setResult(res)
      if (onPlanCompleted) onPlanCompleted(res)
    } catch (err) {
      alert(`推演失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: '680px', maxWidth: '95vw' }}>
        <div className="modal-header">
          <h3>全书世界观与大纲自动推演</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handlePlan} style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500, color: '#374151' }}>
              核心创意种子 / 故事梗概：
            </label>
            <textarea
              rows={4}
              value={seedPrompt}
              onChange={(e) => setSeedPrompt(e.target.value)}
              placeholder="例如：古代架空悬疑，主角是捕快林舟，调查皇城连环失踪案..."
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12.5px', color: '#52525b', fontWeight: 500 }}>题材大类：</label>
              <select value={genre} onChange={(e) => setGenre(e.target.value)} style={{ width: '100%', marginTop: '4px' }}>
                <optgroup label="玄幻奇幻">
                  <option value="东方玄幻/赛博仙侠">东方玄幻 / 赛博仙侠</option>
                  <option value="古典仙侠/修真宗门">古典仙侠 / 宗门正统</option>
                  <option value="西方奇幻/克苏鲁神话">西方奇幻 / 克苏鲁神话</option>
                  <option value="异界大陆/领主种田">异界大陆 / 领主种田</option>
                </optgroup>
                <optgroup label="科幻末世">
                  <option value="赛博朋克/矩阵仿生">赛博朋克 / 义体改造</option>
                  <option value="星际科幻/太空歌剧">星际科幻 / 太空歌剧</option>
                  <option value="末世灾变/异能觉醒">末世灾变 / 避难所生存</option>
                </optgroup>
                <optgroup label="悬疑无限">
                  <option value="悬疑刑侦/心理密室">悬疑刑侦 / 心理密室</option>
                  <option value="无限流/规则怪谈">无限流 / 规则怪谈</option>
                  <option value="民俗怪异/中式克苏鲁">民俗志异 / 探险寻秘</option>
                </optgroup>
                <optgroup label="都市现实">
                  <option value="都市异能/隐世宗门">都市异能 / 鉴宝医圣</option>
                  <option value="商业巨擘/科技创业">商业商战 / 时代风云</option>
                </optgroup>
                <optgroup label="历史架空">
                  <option value="历史权谋/王朝争霸">历史权谋 / 王朝争霸</option>
                  <option value="架空乱世/军事争锋">架空历史 / 谍战暗流</option>
                </optgroup>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12.5px', color: '#52525b', fontWeight: 500 }}>规划卷数：</label>
              <input type="number" min={1} max={5} value={volumes} onChange={(e) => setVolumes(e.target.value)} style={{ width: '100%', marginTop: '4px' }} />
            </div>
            <div>
              <label style={{ fontSize: '12.5px', color: '#52525b', fontWeight: 500 }}>每卷章节：</label>
              <input type="number" min={1} max={8} value={chapters} onChange={(e) => setChapters(e.target.value)} style={{ width: '100%', marginTop: '4px' }} />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
            <button type="button" className="btn-small" onClick={onClose}>取消</button>
            <button type="submit" className="btn-blue" disabled={loading}>
              {loading ? 'AI 正在推演世界观与大纲...' : '开始全书推演'}
            </button>
          </div>
        </form>

        {result && (
          <div style={{ margin: '0 18px 18px', padding: '12px', background: '#fafafa', border: '1px solid #e4e4e7', borderRadius: '6px', fontSize: '13px' }}>
            <span className="status-ready-badge">推演成功</span>
            <p style={{ marginTop: '6px' }}>已创建核心角色：<strong>{result.characters_created?.join('、')}</strong></p>
            <p style={{ marginTop: '4px' }}>已确立主支线：<strong>{result.plot_threads_created?.join('、')}</strong></p>
            <p style={{ marginTop: '4px' }}>总计规划 <strong>{result.total_scenes}</strong> 个场景与节拍契约。</p>
          </div>
        )}
      </div>
    </div>
  )
}
