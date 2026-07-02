import React from 'react'
import { motion } from 'framer-motion'
import { Bot, FileText, Search, BarChart3, ArrowRight, Sparkles, Shield } from 'lucide-react'

const features = [
  {
    icon: Search,
    title: 'Multi-Source RAG',
    desc: 'Ingests PDFs, DOCX, Markdown, HTML, CSV, and JSON — then retrieves with hybrid search.',
  },
  {
    icon: BarChart3,
    title: 'Confidence Scoring',
    desc: 'Every answer shows a confidence gauge, relevance scores, and cited source chunks.',
  },
  {
    icon: Shield,
    title: 'Content Safety',
    desc: 'Built-in PII redaction and content moderation for production-ready deployments.',
  },
  {
    icon: Sparkles,
    title: 'Feedback Loop',
    desc: 'Rate responses and the system learns — thumbs up/down updates retrieval weights.',
  },
]

export default function WelcomeScreen({ onStart }) {
  return (
    <div className="flex-1 flex items-center justify-center p-6 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="max-w-2xl w-full"
      >
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="w-20 h-20 rounded-2xl bg-gradient-to-br from-trace-500 to-purple-600
              flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-trace-500/20"
          >
            <Bot size={40} className="text-white" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white mb-3">
            <span className="gradient-text">Trace</span>
          </h1>
          <p className="text-surface-400 text-sm leading-relaxed max-w-lg mx-auto">
            A transparent support AI that shows its work. Upload knowledge documents,
            ask questions, and get grounded answers with cited sources and confidence scores.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-8">
          {features.map((feature, idx) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + idx * 0.1 }}
              className="glass-panel rounded-xl p-4 hover:border-trace-500/20 transition-all duration-300"
            >
              <feature.icon size={18} className="text-trace-400 mb-2" />
              <h3 className="text-sm font-semibold text-white mb-1">{feature.title}</h3>
              <p className="text-[11px] text-surface-400 leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="text-center"
        >
          <button
            onClick={onStart}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl
              bg-gradient-to-r from-trace-500 to-trace-600 text-white font-medium text-sm
              shadow-lg shadow-trace-500/20 hover:shadow-trace-500/40
              hover:from-trace-400 hover:to-trace-500
              transition-all duration-300"
          >
            Get Started
            <ArrowRight size={16} />
          </button>
          <p className="text-[11px] text-surface-500 mt-3">
            First, upload documents in the sidebar to build your knowledge base.
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}
