import React from 'react'

export function Topbar({ notice }) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">LOCAL CANON & CHAPTER SKELETON</span>
        <h1>NovelAgent</h1>
      </div>
      <span className="status">{notice}</span>
    </header>
  )
}
