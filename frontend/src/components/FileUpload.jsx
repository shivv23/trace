import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle, Loader2, FileText, FileSpreadsheet, FileJson } from 'lucide-react'
import { uploadDocument } from '../utils/api'
import clsx from 'clsx'

export default function FileUpload({ onUploadComplete }) {
  const [uploads, setUploads] = useState([])

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      const id = `${file.name}-${Date.now()}`
      setUploads(prev => [...prev, {
        id,
        name: file.name,
        size: file.size,
        status: 'uploading',
        progress: 0,
      }])

      try {
        const result = await uploadDocument(file, (progress) => {
          setUploads(prev => prev.map(u =>
            u.id === id ? { ...u, progress } : u
          ))
        })

        setUploads(prev => prev.map(u =>
          u.id === id ? {
            ...u,
            status: 'done',
            progress: 100,
            result,
          } : u
        ))
        onUploadComplete?.(result)
      } catch (err) {
        setUploads(prev => prev.map(u =>
          u.id === id ? { ...u, status: 'error', error: err.message } : u
        ))
      }
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'text/html': ['.html', '.htm'],
    },
    maxSize: 20 * 1024 * 1024,
  })

  const removeUpload = (id) => {
    setUploads(prev => prev.filter(u => u.id !== id))
  }

  const getFileIcon = (name) => {
    const ext = name.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf': return <FileText size={16} className="text-red-400" />
      case 'docx': return <FileText size={16} className="text-blue-400" />
      case 'csv': return <FileSpreadsheet size={16} className="text-green-400" />
      case 'json': return <FileJson size={16} className="text-amber-400" />
      case 'md': return <FileText size={16} className="text-trace-400" />
      default: return <File size={16} className="text-surface-400" />
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={clsx(
          'upload-zone p-6 text-center cursor-pointer transition-all duration-300',
          isDragActive && 'active border-trace-500/50 bg-trace-500/5',
        )}
      >
        <input {...getInputProps()} />
        <motion.div
          animate={{ scale: isDragActive ? 1.05 : 1 }}
          className="flex flex-col items-center gap-2"
        >
          <div className={clsx(
            'w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300',
            isDragActive ? 'bg-trace-500/20 scale-110' : 'bg-surface-800/50'
          )}>
            <Upload size={22} className={isDragActive ? 'text-trace-400' : 'text-surface-400'} />
          </div>
          <div>
            <p className="text-sm text-surface-300">
              {isDragActive ? 'Drop files here' : 'Drag & drop files'}
            </p>
            <p className="text-[10px] text-surface-500 mt-0.5">
              PDF, DOCX, TXT, MD, JSON, CSV, HTML — up to 20 MB
            </p>
          </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {uploads.map((upload) => (
          <motion.div
            key={upload.id}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-3 p-2.5 rounded-lg bg-surface-800/40 border border-surface-700/20"
          >
            {getFileIcon(upload.name)}

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-surface-200 truncate">{upload.name}</span>
                <span className="text-[10px] text-surface-500 shrink-0">{formatSize(upload.size)}</span>
              </div>

              {upload.status === 'uploading' && (
                <div className="mt-1.5 h-1 bg-surface-700/50 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${upload.progress}%` }}
                    className="h-full bg-gradient-to-r from-trace-500 to-trace-400 rounded-full"
                  />
                </div>
              )}

              {upload.status === 'done' && upload.result && (
                <p className="text-[10px] text-emerald-400 mt-0.5">
                  {upload.result.chunk_count} chunks indexed
                </p>
              )}

              {upload.status === 'error' && (
                <p className="text-[10px] text-red-400 mt-0.5">{upload.error || 'Upload failed'}</p>
              )}
            </div>

            <div className="shrink-0">
              {upload.status === 'uploading' && <Loader2 size={16} className="animate-spin text-trace-400" />}
              {upload.status === 'done' && <CheckCircle size={16} className="text-emerald-400" />}
              {upload.status === 'error' && <AlertCircle size={16} className="text-red-400" />}
              {upload.status !== 'uploading' && (
                <button onClick={() => removeUpload(upload.id)}
                  className="p-1 hover:bg-surface-700/50 rounded transition-colors">
                  <X size={14} className="text-surface-500" />
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
