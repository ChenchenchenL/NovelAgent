import React, { useState } from 'react'
import { useModelConfig } from '../hooks/useModelConfig'

export function ModelConfigPanel() {
  const { config, loading, testResult, saveConfig, testConnection, removeApiKey } = useModelConfig()
  const [endpoint, setEndpoint] = useState(config.endpoint || '')
  const [t1, setT1] = useState(config.models?.T1 || '')
  const [t2, setT2] = useState(config.models?.T2 || '')
  const [t3, setT3] = useState(config.models?.T3 || '')
  const [apiKey, setApiKey] = useState('')
  const [msg, setMsg] = useState('')

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      await saveConfig({
        endpoint: endpoint.trim(),
        models: { T1: t1.trim() || 'small-extraction', T2: t2.trim() || 'medium-planning', T3: t3.trim() || 'frontier-writing' },
        apiKey: apiKey.trim() || undefined,
      })
      setMsg('配置已保存')
      setApiKey('')
    } catch (err) {
      setMsg(`保存失败: ${err.message}`)
    }
  }

  const handleTest = async () => {
    const res = await testConnection({ endpoint, api_key: apiKey || undefined })
    setMsg(res.status === 'ok' ? '连接成功！' : `连接失败: ${res.error}`)
  }

  return (
    <div className="model-config-panel panel">
      <h3>AI 模型服务配置</h3>
      <form onSubmit={handleSave}>
        <div className="form-group">
          <label>API Endpoint</label>
          <input value={endpoint} placeholder="https://api.openai.com/v1" onChange={(e) => setEndpoint(e.target.value)} />
        </div>
        <div className="form-group">
          <label>API Key {config.has_key ? '（已设置）' : '（未设置）'}</label>
          <input type="password" value={apiKey} placeholder="sk-..." onChange={(e) => setApiKey(e.target.value)} />
        </div>
        <div className="model-tier-grid">
          <div><label>T1 抽取模型</label><input value={t1} placeholder="gpt-4o-mini" onChange={(e) => setT1(e.target.value)} /></div>
          <div><label>T2 规划模型</label><input value={t2} placeholder="gpt-4o" onChange={(e) => setT2(e.target.value)} /></div>
          <div><label>T3 写作模型</label><input value={t3} placeholder="claude-3-5-sonnet" onChange={(e) => setT3(e.target.value)} /></div>
        </div>
        <div className="actions">
          <button type="submit" disabled={loading}>保存配置</button>
          <button type="button" onClick={handleTest} disabled={loading}>测试连接</button>
          {config.has_key && <button type="button" className="btn-danger" onClick={removeApiKey}>删除密钥</button>}
        </div>
        {msg && <div className="config-msg">{msg}</div>}
      </form>
    </div>
  )
}
