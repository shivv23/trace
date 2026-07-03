import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, ChevronDown, ChevronUp, Percent } from 'lucide-react'
import clsx from 'clsx'

export default function SourceCard({ source, index, isActive }) {
  const [expanded, setExpanded] = useState(false)
  const score = source.relevance_score || 0
  const normalizedScore = typeof score === 'number'
    ? Math.max(0, Math.min(1, (score + 1) / 2))
    : 0.5
  const scorePercent = Math.round(normalizedScore * 100)

  const cardRef = useRef(null)

  useEffect(() => {
    if (isActive && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [isActive])

  function getFileIcon(type) {
    switch (type?.toLowerCase()) {
      case '.pdf': return 'PDF'
      case '.docx': return 'DOC'
      case '.md': return 'MD'
      case '.csv': return 'CSV'
      case '.json': return 'JSON'
      case '.html':
      case '.htm': return 'HTML'
      case '.txt': return 'TXT'
      default: return 'FILE'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="source-card group"
      ref={cardRef}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left transition-all duration-200 ${
          isActive
            ? 'bg-trace-500/15 border-trace-500/40 shadow-sm shadow-trace-500/10'
            : 'bg-surface-800/30 border-surface-700/20 hover:bg-surface-800/60 hover:border-surface-700/40'
        } border`}
      >
        <div className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 transition-all duration-200 ${
          isActive
            ? 'bg-trace-500/20 border-trace-500/40'
            : 'bg-trace-500/10 border-trace-500/20'
        } border`}>
          <span className="text-[10px] font-bold text-trace-400">{getFileIcon(source.file_type)}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-surface-200 truncate">
              {source.document_name || 'Unknown'}
            </span>
            {source.page_number && (
              <span className="text-[10px] text-surface-500 shrink-0">p.{source.page_number}</span>
            )}
          </div>

          <p className={clsx(
            'text-[11px] text-surface-400 leading-relaxed mt-0.5 transition-all duration-200',
            !expanded && 'line-clamp-2'
          )}>
            {source.content}
          </p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0 mt-0.5">
          <div className={clsx(
            'flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium',
            scorePercent >= 70 ? 'bg-emerald-500/10 text-emerald-400' :
            scorePercent >= 40 ? 'bg-amber-500/10 text-amber-400' :
            'bg-surface-700/30 text-surface-400'
          )}>
            <Percent size={10} />
            {scorePercent}%
          </div>
          {expanded ? <ChevronUp size={14} className="text-surface-500" /> : <ChevronDown size={14} className="text-surface-500" />}
        </div>
      </button>

      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="px-3 pb-2"
        >
          <div className="mt-1.5 p-2.5 rounded-lg bg-surface-900/50 border border-surface-800/30">
            <pre className="text-[11px] text-surface-400 leading-relaxed whitespace-pre-wrap font-sans">
              {source.content}
            </pre>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
