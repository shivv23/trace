import React, { useState } from 'react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import ConfidenceGauge from './ConfidenceGauge'
import SourceCard from './SourceCard'
import FeedbackButtons from './FeedbackButtons'
import clsx from 'clsx'

export default function MessageBubble({ message, onRate }) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false)
  const isUser = message.role === 'user'
  const hasSources = message.sources && message.sources.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={clsx(
        'flex gap-3 py-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-trace-500/20 to-purple-600/20 flex items-center justify-center shrink-0 border border-trace-500/10 mt-1">
          <Bot size={16} className="text-trace-400" />
        </div>
      )}

      <div className={clsx(
        'max-w-[80%] min-w-0',
        isUser && 'order-1'
      )}>
        <div className={clsx(
          'px-4 py-3',
          isUser
            ? 'bg-gradient-to-br from-trace-600 to-trace-700 text-white rounded-2xl rounded-tr-md'
            : 'glass-panel rounded-2xl rounded-tl-md'
        )}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer"
                      className="text-trace-400 hover:text-trace-300 underline underline-offset-2">
                      {children} <ExternalLink size={12} className="inline" />
                    </a>
                  ),
                  code: ({ children }) => (
                    <code className="bg-surface-800/60 px-1.5 py-0.5 rounded text-[13px] font-mono text-trace-300">
                      {children}
                    </code>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-3 px-1">
              {message.confidence && <ConfidenceGauge confidence={message.confidence} size="sm" />}

              <FeedbackButtons
                rating={message.rating}
                onRate={onRate}
              />

              {message.processingTime && (
                <span className="text-[10px] text-surface-500 ml-auto">
                  {(message.processingTime / 1000).toFixed(1)}s
                </span>
              )}
            </div>

            {hasSources && (
              <div>
                <button
                  onClick={() => setSourcesExpanded(!sourcesExpanded)}
                  className="flex items-center gap-1.5 text-[11px] text-surface-400 hover:text-surface-200
                    transition-colors px-1 py-0.5 rounded hover:bg-surface-800/30"
                >
                  {sourcesExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                </button>

                <AnimateSection expanded={sourcesExpanded}>
                  <div className="space-y-1.5 mt-1.5">
                    {message.sources.map((source, idx) => (
                      <SourceCard key={source.chunk_id} source={source} index={idx} />
                    ))}
                  </div>
                </AnimateSection>
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-surface-600 to-surface-700 flex items-center justify-center shrink-0 border border-surface-600/30 mt-1">
          <User size={16} className="text-surface-300" />
        </div>
      )}
    </motion.div>
  )
}

function AnimateSection({ expanded, children }) {
  return (
    <div
      className="grid overflow-hidden transition-all duration-200 ease-in-out"
      style={{
        gridTemplateRows: expanded ? '1fr' : '0fr',
        opacity: expanded ? 1 : 0,
        transition: 'grid-template-rows 0.2s ease-in-out, opacity 0.2s ease-in-out',
      }}
    >
      <div className="min-h-0">
        {children}
      </div>
    </div>
  )
}
