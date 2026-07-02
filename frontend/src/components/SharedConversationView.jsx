import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bot, User, Clock, AlertCircle, Share2 } from 'lucide-react'
import { getSharedConversation } from '../utils/api'

export default function SharedConversationView({ shareId, onBack }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!shareId) return
    setLoading(true)
    getSharedConversation(shareId)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [shareId])

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href)
      .then(() => alert('Link copied!'))
      .catch(() => {})
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-surface-950">
        <div className="w-6 h-6 border-2 border-trace-500/30 border-t-trace-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-surface-950">
        <div className="text-center">
          <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-sm text-surface-400">This shared conversation could not be found or has been removed.</p>
          <button onClick={onBack} className="mt-4 px-4 py-2 bg-trace-600 text-white text-sm rounded-lg hover:bg-trace-500">
            Go Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-950">
      <header className="h-14 flex items-center justify-between px-4 border-b border-surface-800/50 bg-surface-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-trace-500 to-purple-600 flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-white">Trace</span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-surface-500">
          <Clock size={12} />
          <span>Shared conversation</span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="glass-panel rounded-xl px-4 py-3 mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-white">{data?.title || 'Shared conversation'}</h1>
            <p className="text-[10px] text-surface-500 mt-0.5">{data?.messages?.length || 0} messages</p>
          </div>
          <button onClick={handleCopyLink} className="flex items-center gap-1.5 px-3 py-1.5 bg-trace-600/20 text-trace-400 text-xs rounded-lg hover:bg-trace-600/30 transition-colors">
            <Share2 size={12} />
            Copy link
          </button>
        </div>

        <div className="space-y-4">
          {data?.messages?.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.04 }}
              className={`flex gap-3 ${msg.role === 'user' ? '' : 'flex-row-reverse'}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === 'user' ? 'bg-surface-800' : 'bg-trace-500/20'
              }`}>
                {msg.role === 'user' ? <User size={14} className="text-surface-400" /> : <Bot size={14} className="text-trace-400" />}
              </div>
              <div className={`flex-1 max-w-[85%] ${msg.role === 'assistant' ? 'flex flex-col items-end' : ''}`}>
                <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-surface-800/80 text-surface-200 rounded-tl-sm'
                    : 'bg-trace-500/10 text-surface-200 rounded-tr-sm border border-trace-500/10'
                }`}>
                  {msg.content}
                </div>
                <span className="text-[10px] text-surface-600 mt-1 px-1">{msg.role === 'user' ? 'You' : 'Trace'}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  )
}
