import React from 'react'

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[11px] text-surface-400 mr-1">Thinking</span>
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  )
}
