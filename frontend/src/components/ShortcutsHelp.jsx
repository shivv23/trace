import { motion } from 'framer-motion'
import { X, Search, MessageSquare, Share2, Settings, Download, Trash2, Edit3, Keyboard } from 'lucide-react'

const shortcuts = [
  { keys: ['Ctrl', 'K'], desc: 'Search conversations', icon: Search },
  { keys: ['?'], desc: 'Toggle this help menu', icon: Keyboard },
  { keys: ['Enter'], desc: 'Send message', icon: MessageSquare },
  { keys: ['Shift', 'Enter'], desc: 'New line in message', icon: MessageSquare },
  { keys: ['Esc'], desc: 'Close modals / cancel', icon: X },
]

export default function ShortcutsHelp({ open, onClose }) {
  if (!open) return null
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.97 }}
        className="w-full max-w-sm mx-4 bg-surface-900 border border-surface-700/50 rounded-2xl shadow-2xl p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center">
              <Keyboard size={16} className="text-trace-400" />
            </div>
            <h2 className="text-sm font-semibold text-white">Keyboard Shortcuts</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-800 text-surface-500 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-2">
          {shortcuts.map((s, idx) => (
            <div key={idx} className="flex items-center justify-between py-2 px-1">
              <div className="flex items-center gap-2.5">
                <s.icon size={14} className="text-surface-500" />
                <span className="text-xs text-surface-300">{s.desc}</span>
              </div>
              <div className="flex items-center gap-1">
                {s.keys.map((k, ki) => (
                  <span key={ki} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-800 text-surface-300 border border-surface-700/50">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-3 border-t border-surface-800/50">
          <p className="text-[10px] text-surface-500 text-center">
            Press <kbd className="px-1 py-0.5 rounded text-[10px] bg-surface-800 text-surface-300 border border-surface-700/50">?</kbd> anytime to toggle this menu
          </p>
        </div>
      </motion.div>
    </motion.div>
  )
}
