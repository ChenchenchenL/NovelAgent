import React, { useState, useEffect } from 'react'
import { useModelConfig } from '../../hooks/useModelConfig'

const PRESETS = [
  { name: 'DeepSeek', endpoint: 'https://api.deepseek.com', model: 'deepseek-chat' },
  { name: 'OpenAI', endpoint: 'https://api.openai.com/v1', model: 'gpt-4o' },
  { name: '硅基流动', endpoint: 'https://api.siliconflow.cn/v1', model: 'deepseek-ai/DeepSeek-V3' },
  { name: '本地 Ollama', endpoint: 'http://localhost:11434/v1', model: 'qwen2.5:7b' },
]

export function ModelConfigModal({ isOpen, onClose }) {
  const { config, loading, saveConfig, testConnection, removeApiKey } = useModelConfig()
  const [endpoint, setEndpoint] = useState('')
  const [modelName, setModelName] = useState('deepseek-chat')
  const [apiKey, setApiKey] = useState('')
  const [msg, setMsg] = useState('')
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    if (config) {
      setEndpoint(config.endpoint || 'https://api.deepseek.com')
      setModelName(config.models?.T3 || config.models?.T2 || 'deepseek-chat')
    }
  }, [config])

  if (!isOpen) return null

  const handleApplyPreset = (p) => {
    setEndpoint(p.endpoint)
    setModelName(p.model)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      const chosen = modelName.trim() || 'deepseek-chat'
      await saveConfig({
        endpoint: endpoint.trim(),
        models: { T1: chosen, T2: chosen, T3: chosen },
        apiKey: apiKey.trim() || undefined,
      })
      setMsg('模型服务已成功保存！')
      setApiKey('')
    } catch (err) { setMsg(`保存失败: ${err.message}`) }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const res = await testConnection({ endpoint: endpoint.trim(), api_key: apiKey.trim() || undefined })
      setMsg(res.status === 'ok' ? '连接成功！模型响应正常。' : `连接失败: ${res.error}`)
    } catch (err) { setMsg(`测试异常: ${err.message}`) }
    finally { setTesting(false) }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: '560px', maxWidth: '94vw' }}>
        <div className="modal-header">
          <h3>AI 创作大模型设置</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSave} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', color: '#71717a', fontWeight: 600, display: 'block', marginBottom: '6px' }}>快速预设服务商：</label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {PRESETS.map((p) => (
                <button key={p.name} type="button" className="btn-small" onClick={() => handleApplyPreset(p)}>
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12.5px', color: '#374151', fontWeight: 600 }}>API 接口地址 (Base URL)</label>
            <input value={endpoint} placeholder="例如: https://api.deepseek.com" onChange={(e) => setEndpoint(e.target.value)} style={{ width: '100%', marginTop: '4px' }} required />
          </div>

          <div>
            <label style={{ fontSize: '12.5px', color: '#374151', fontWeight: 600 }}>API Key 密钥 {config?.has_key ? '（已配置）' : '（未配置）'}</label>
            <input type="password" value={apiKey} placeholder={config?.has_key ? '留空表示保持当前密钥不变' : '请输入 API Key'} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginTop: '4px' }} />
          </div>

          <div>
            <label style={{ fontSize: '12.5px', color: '#374151', fontWeight: 600 }}>小说创作大模型名称</label>
            <input value={modelName} placeholder="例如: deepseek-chat, gpt-4o, claude-3-5-sonnet" onChange={(e) => setModelName(e.target.value)} style={{ width: '100%', marginTop: '4px' }} required />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
            <div>{config?.has_key && <button type="button" className="btn-small btn-danger" onClick={removeApiKey}>清除密钥</button>}</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button type="button" className="btn-small" onClick={handleTest} disabled={loading || testing}>{testing ? '测试中...' : '测试连接'}</button>
              <button type="submit" className="btn-blue" disabled={loading}>保存配置</button>
            </div>
          </div>
          {msg && <div style={{ padding: '8px 12px', background: '#fafafa', border: '1px solid #e4e4e7', borderRadius: '4px', fontSize: '12.5px', color: msg.includes('失败') ? '#ef4444' : '#059669' }}>{msg}</div>}
        </form>
      </div>
    </div>
  )
}
