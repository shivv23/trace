import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, MessageSquare, X, ArrowRight, Loader2 } from 'lucide-react'
import { searchConversations } from '../utils/api'

export default function SearchModal({ open, onClose, onSelectConversation }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
      setQuery('')
      setResults([])
    }
  }, [open])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query || query.length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchConversations(query)
        setResults(data.results || [])
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.97 }}
        transition={{ duration: 0.15 }}
        className="w-full max-w-xl mx-4 bg-surface-900 border border-surface-700/50 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-800">
          {loading ? (
            <Loader2 size={16} className="text-surface-500 animate-spin shrink-0" />
          ) : (
            <Search size={16} className="text-surface-500 shrink-0" />
          )}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search conversations..."
            className="flex-1 bg-transparent text-sm text-white placeholder-surface-500 outline-none"
          />
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-surface-600 bg-surface-800 px-1.5 py-0.5 rounded">ESC</span>
            <button onClick={onClose} className="p-1 rounded hover:bg-surface-800 text-surface-500 hover:text-white">
              <X size={14} />
            </button>
          </div>
        </div>

        <div className="max-h-80 overflow-y-auto scrollbar-hide">
          {results.length === 0 && query.length >= 2 && !loading && (
            <div className="px-4 py-8 text-center">
              <p className="text-xs text-surface-500">No results found</p>
            </div>
          )}
          <AnimatePresence>
            {results.map((r, idx) => (
              <motion.button
                key={r.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.03 }}
                onClick={() => {
                  onSelectConversation(r.conversation_id)
                  onClose()
                }}
                className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-surface-800/60 transition-colors border-b border-surface-800/30 last:border-0"
              >
                <MessageSquare size={14} className="mt-0.5 shrink-0 text-surface-500" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-surface-500 mb-0.5">
                    {r.conv_title || r.conversation_id?.slice(0, 8)}
                    <span className="text-surface-600 mx-1">·</span>
                    <span className={r.role === 'user' ? 'text-trace-400' : 'text-purple-400'}>
                      {r.role}
                    </span>
                  </p>
                  <p className="text-sm text-white truncate">{r.content}</p>
                </div>
                <ArrowRight size={14} className="shrink-0 text-surface-600 mt-1 opacity-0 group-hover:opacity-100" />
              </motion.button>
            ))}
          </AnimatePresence>
        </div>
      </motion.div>
    </motion.div>
  )
}
