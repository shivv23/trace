import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Bot, LogIn, User, Lock, AlertCircle, Loader2 } from 'lucide-react'

export default function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password) return
    setLoading(true)
    setError(null)
    try {
      const { login } = await import('../utils/api')
      await login(username, password)
      onLogin()
    } catch (err) {
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-surface-950 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-trace-500/5 via-transparent to-purple-600/5" />
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="relative w-full max-w-sm mx-4"
      >
        <div className="glass-panel rounded-2xl p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-trace-500 to-purple-600 flex items-center justify-center shadow-xl shadow-trace-500/20 mb-4">
              <Bot size={28} className="text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">Trace</h1>
            <p className="text-sm text-surface-400 mt-1">Transparent Support AI</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-surface-500" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                autoFocus
                className="w-full bg-surface-800/60 border border-surface-700/30 rounded-xl pl-10 pr-4 py-3
                  text-sm text-white placeholder-surface-500
                  focus:border-trace-500/50 focus:ring-1 focus:ring-trace-500/20
                  transition-all duration-200"
              />
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-surface-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full bg-surface-800/60 border border-surface-700/30 rounded-xl pl-10 pr-4 py-3
                  text-sm text-white placeholder-surface-500
                  focus:border-trace-500/50 focus:ring-1 focus:ring-trace-500/20
                  transition-all duration-200"
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"
              >
                <AlertCircle size={14} className="text-red-400 shrink-0" />
                <span className="text-xs text-red-400">{error}</span>
              </motion.div>
            )}

            <motion.button
              type="submit"
              disabled={!username.trim() || !password || loading}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 rounded-xl flex items-center justify-center gap-2
                bg-gradient-to-r from-trace-500 to-trace-600 text-white font-medium text-sm
                shadow-lg shadow-trace-500/20 hover:shadow-trace-500/30
                disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <LogIn size={18} />
              )}
              {loading ? 'Signing in...' : 'Sign In'}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
