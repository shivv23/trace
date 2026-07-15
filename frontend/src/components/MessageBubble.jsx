import React, { useState } from 'react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, ChevronDown, ChevronUp, ExternalLink, Download, Lightbulb, Globe, Search } from 'lucide-react'
import ConfidenceGauge from './ConfidenceGauge'
import SourceCard from './SourceCard'
import FeedbackButtons from './FeedbackButtons'
import clsx from 'clsx'

function CitationLink({ idx, activeIdx, onClick, children }) {
  const isActive = activeIdx === idx
  return (
    <button
      onClick={(e) => { e.preventDefault(); onClick(idx) }}
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium transition-all duration-200 mx-0.5 align-middle ${
        isActive
          ? 'bg-trace-500/25 text-trace-300 border border-trace-500/40 scale-105 shadow-sm shadow-trace-500/10'
          : 'bg-surface-800/60 text-surface-400 border border-surface-700/30 hover:bg-trace-500/10 hover:text-trace-400'
      }`}
    >
      [{idx + 1}]
    </button>
  )
}

function renderContentWithCitations(content, activeIdx, onSourceClick) {
  const parts = content.split(/(\[Source \d+\])/g)
  return parts.map((part, i) => {
    const match = part.match(/\[Source (\d+)\]/)
    if (match) {
      const idx = parseInt(match[1]) - 1
      return (
        <CitationLink key={`cite-${i}`} idx={idx} activeIdx={activeIdx} onClick={onSourceClick}>
          {match[1]}
        </CitationLink>
      )
    }
    if (!part) return null
    return (
      <ReactMarkdown
        key={`md-${i}`}
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
          p: ({ children }) => <span className="inline">{children}</span>,
        }}
      >
        {part}
      </ReactMarkdown>
    )
  })
}


export default function MessageBubble({ message, onRate, onSuggestedClick }) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false)
  const [activeCitation, setActiveCitation] = useState(null)
  const isUser = message.role === 'user'
  const hasSources = message.sources && message.sources.length > 0
  const hasSuggestions = message.suggestedQuestions && message.suggestedQuestions.length > 0

  const handleExport = () => {
    const text = `**${message.role === 'user' ? 'You' : 'Trace'}**: ${message.content}`
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trace-message-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCitationClick = (idx) => {
    setActiveCitation(activeCitation === idx ? null : idx)
    if (hasSources && message.sources[idx]) {
      setSourcesExpanded(true)
    }
  }

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
            <div className="prose prose-invert prose-sm max-w-none [&>p]:mb-0">
              {renderContentWithCitations(message.content, activeCitation, handleCitationClick)}
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

              <button
                onClick={handleExport}
                className="p-1 rounded hover:bg-surface-800 text-surface-500 hover:text-surface-300 transition-colors"
                title="Download this message"
              >
                <Download size={12} />
              </button>

              <div className="flex items-center gap-1.5 ml-auto">
                {message.language && message.language !== 'en' && (
                  <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-surface-800/60 text-surface-400 border border-surface-700/30">
                    <Globe size={10} />
                    {message.language.toUpperCase()}
                  </span>
                )}
                {message.webSearchUsed && (
                  <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-trace-500/10 text-trace-400 border border-trace-500/20">
                    <Search size={10} />
                    Web
                  </span>
                )}
                {message.processingTime && (
                  <span className="text-[10px] text-surface-500">
                    {(message.processingTime / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
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
                      <SourceCard key={source.chunk_id} source={source} index={idx} isActive={activeCitation === idx} />
                    ))}
                  </div>
                </AnimateSection>
              </div>
            )}

            {hasSuggestions && (
              <div className="pt-1">
                <div className="flex items-center gap-1.5 mb-1.5 px-1">
                  <Lightbulb size={11} className="text-surface-500" />
                  <span className="text-[10px] text-surface-500 font-medium">Follow-up questions</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {message.suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSuggestedClick?.(q)}
                      className="px-2.5 py-1.5 text-[11px] rounded-lg bg-surface-800/50 border border-surface-700/30
                        text-surface-400 hover:text-white hover:border-trace-500/30 hover:bg-trace-500/5
                        transition-all duration-200 text-left max-w-full"
                    >
                      {q}
                    </button>
                  ))}
                </div>
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
