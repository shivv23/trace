import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, RefreshCw } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { listDocuments } from '../utils/api'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

export default function ChatWidget() {
  const [input, setInput] = useState('')
  const [docNames, setDocNames] = useState([])
  const { messages, isLoading, error, send, rateMessage, clear } = useChat()
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    listDocuments().then(docs => setDocNames(docs.map(d => d.name))).catch(() => {})
  }, [])

  const suggestions = docNames.length > 0
    ? [
        `What does "${docNames[0]}" contain?`,
        'How does the confidence scoring work?',
        'Summarize the uploaded documents',
      ]
    : [
        'What file formats are supported?',
        'How does the confidence scoring work?',
        'Summarize the uploaded documents',
      ]

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    send(input.trim())
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {messages.length === 0 && !isLoading ? (
        <div className="flex-1 flex items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-md"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-trace-500/20 to-purple-600/20 flex items-center justify-center mx-auto mb-5 border border-trace-500/10">
              <Sparkles size={28} className="text-trace-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Ask anything</h2>
            <p className="text-sm text-surface-400 leading-relaxed">
              Upload documents to the knowledge base, then ask questions.
              Trace will search, cite sources, and show confidence for every answer.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => { send(suggestion); setInput('') }}
                  className="px-3 py-1.5 text-xs rounded-full bg-surface-800/60 border border-surface-700/30
                    text-surface-300 hover:text-white hover:border-trace-500/30 hover:bg-trace-500/5
                    transition-all duration-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </motion.div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1 scrollbar-hide">
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onRate={(rating) => rateMessage(msg.messageIndex, rating)}
              />
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="glass-panel rounded-2xl rounded-bl-md px-4 py-3 max-w-[85%]">
                <TypingIndicator />
              </div>
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center"
            >
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2 text-xs text-red-400">
                {error}
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="shrink-0 border-t border-surface-800/50 bg-surface-900/30 px-4 py-3">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your knowledge base..."
              rows={1}
              className="w-full bg-surface-800/60 border border-surface-700/30 rounded-xl px-4 py-3
                text-sm text-white placeholder-surface-500 resize-none
                focus:border-trace-500/50 focus:ring-1 focus:ring-trace-500/20
                transition-all duration-200"
              style={{ minHeight: '44px', maxHeight: '120px' }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
          </div>
          <motion.button
            type="submit"
            disabled={!input.trim() || isLoading}
            whileTap={{ scale: 0.95 }}
            className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 ${
              input.trim() && !isLoading
                ? 'bg-gradient-to-r from-trace-500 to-trace-600 text-white shadow-lg shadow-trace-500/20 hover:shadow-trace-500/30'
                : 'bg-surface-800 text-surface-500 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <RefreshCw size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </motion.button>
        </form>
        <p className="text-[10px] text-surface-500 text-center mt-2">
          Answers are grounded in your knowledge base. Sources and confidence scores shown for every response.
        </p>
      </div>
    </div>
  )
}
