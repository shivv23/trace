import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, FileText, Trash2, RefreshCw, Inbox, ChevronRight } from 'lucide-react'
import { listDocuments, deleteDocument } from '../utils/api'
import FileUpload from './FileUpload'
import clsx from 'clsx'

export default function KnowledgePanel() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  const handleUploadComplete = (result) => {
    fetchDocuments()
  }

  const handleDelete = async (docId) => {
    setDeleting(docId)
    try {
      await deleteDocument(docId)
      setDocuments(prev => prev.filter(d => d.id !== docId))
    } catch (err) {
      console.error('Delete failed:', err)
    } finally {
      setDeleting(null)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="shrink-0 p-4 border-b border-surface-800/50">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-trace-500/20 to-purple-600/20 flex items-center justify-center">
            <Database size={15} className="text-trace-400" />
          </div>
          <h2 className="text-sm font-semibold text-white">Knowledge Base</h2>
          <span className="text-[10px] text-surface-500 ml-auto">
            {documents.length} file{documents.length !== 1 ? 's' : ''}
          </span>
        </div>
        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw size={18} className="animate-spin text-surface-500" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-xl bg-surface-800/40 flex items-center justify-center mx-auto mb-3">
              <Inbox size={22} className="text-surface-500" />
            </div>
            <p className="text-xs text-surface-500">No documents indexed yet</p>
            <p className="text-[10px] text-surface-600 mt-1">Upload files above to build your knowledge base</p>
          </div>
        ) : (
          <div className="space-y-1">
            <AnimatePresence>
              {documents.map((doc, idx) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  className="group flex items-center gap-2.5 p-2.5 rounded-lg
                    hover:bg-surface-800/30 transition-all duration-200"
                >
                  <div className={clsx(
                    'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
                    doc.type === '.pdf' ? 'bg-red-500/10' :
                    doc.type === '.docx' ? 'bg-blue-500/10' :
                    doc.type === '.md' ? 'bg-trace-500/10' :
                    doc.type === '.json' ? 'bg-amber-500/10' :
                    doc.type === '.csv' ? 'bg-green-500/10' :
                    doc.type === '.txt' ? 'bg-gray-500/10' :
                    doc.type === '.html' || doc.type === '.htm' ? 'bg-orange-500/10' :
                    'bg-surface-700/30'
                  )}>
                    <FileText size={15} className={
                      doc.type === '.pdf' ? 'text-red-400' :
                      doc.type === '.docx' ? 'text-blue-400' :
                      doc.type === '.md' ? 'text-trace-400' :
                      doc.type === '.json' ? 'text-amber-400' :
                      doc.type === '.csv' ? 'text-green-400' :
                      doc.type === '.txt' ? 'text-gray-400' :
                      doc.type === '.html' || doc.type === '.htm' ? 'text-orange-400' :
                      'text-surface-400'
                    } />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-surface-200 truncate group-hover:text-white transition-colors">
                      {doc.name}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-surface-500">{formatSize(doc.size_bytes)}</span>
                      <ChevronRight size={8} className="text-surface-600" />
                      <span className="text-[10px] text-surface-500">{doc.chunk_count} chunks</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deleting === doc.id}
                    className="p-1.5 rounded-md opacity-60 md:opacity-0 group-hover:opacity-100
                      hover:bg-red-500/10 transition-all duration-200"
                  >
                    {deleting === doc.id
                      ? <RefreshCw size={13} className="animate-spin text-red-400" />
                      : <Trash2 size={13} className="text-surface-500 hover:text-red-400" />
                    }
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  )
}
