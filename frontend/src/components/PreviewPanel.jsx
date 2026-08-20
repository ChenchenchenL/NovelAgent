import React from 'react'

function escapeHtml(text = '') {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function renderMarkdown(md = '') {
  if (!md) return '<p class="empty-text">正文为空</p>'

  const lines = md.split('\n')
  const html = []
  let inCode = false
  let codeBuffer = []

  for (const rawLine of lines) {
    if (rawLine.trim().startsWith('```')) {
      if (inCode) {
        html.push(`<pre><code>${codeBuffer.join('\n')}</code></pre>`)
        codeBuffer = []
        inCode = false
      } else {
        inCode = true
      }
      continue
    }

    if (inCode) {
      codeBuffer.push(escapeHtml(rawLine))
      continue
    }

    const line = escapeHtml(rawLine)
    if (line.startsWith('### ')) {
      html.push(`<h3>${line.slice(4)}</h3>`)
    } else if (line.startsWith('## ')) {
      html.push(`<h2>${line.slice(3)}</h2>`)
    } else if (line.startsWith('# ')) {
      html.push(`<h1>${line.slice(2)}</h1>`)
    } else if (line.startsWith('&gt; ')) {
      html.push(`<blockquote>${line.slice(5)}</blockquote>`)
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      html.push(`<li>${line.slice(2)}</li>`)
    } else if (line.trim() === '') {
      html.push('<div class="md-spacer"></div>')
    } else {
      const formatted = line
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
      html.push(`<p>${formatted}</p>`)
    }
  }

  if (inCode && codeBuffer.length > 0) {
    html.push(`<pre><code>${codeBuffer.join('\n')}</code></pre>`)
  }

  return html.join('\n')
}

export function PreviewPanel({ content }) {
  return (
    <div
      className="markdown-preview-pane"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  )
}
