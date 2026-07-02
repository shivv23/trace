import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Menu, X, FileText, Settings, LogOut } from 'lucide-react'
import ChatWidget from './components/ChatWidget'
import KnowledgePanel from './components/KnowledgePanel'
import WelcomeScreen from './components/WelcomeScreen'
import LoginScreen from './components/LoginScreen'
import { healthCheck, getStoredUser, isAuthenticated, logout } from './utils/api'

export default function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showWelcome, setShowWelcome] = useState(true)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [user, setUser] = useState(null)

  useEffect(() => {
    const stored = getStoredUser()
    const authed = isAuthenticated()
    if (authed && stored) {
      setAuthenticated(true)
      setUser(stored)
    }
    setCheckingAuth(false)
  }, [])

  useEffect(() => {
    if (!authenticated) return
    healthCheck()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'))
  }, [authenticated])

  const handleLogin = () => {
    setAuthenticated(true)
    setUser(getStoredUser())
  }

  const handleLogout = () => {
    logout()
    setAuthenticated(false)
    setUser(null)
    setShowWelcome(true)
  }

  const handleStartChat = () => setShowWelcome(false)

  if (checkingAuth) {
    return (
      <div className="h-screen flex items-center justify-center bg-surface-950">
        <div className="w-6 h-6 border-2 border-trace-500/30 border-t-trace-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (!authenticated) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <div className="h-screen flex flex-col bg-surface-950 overflow-hidden">
      <header className="h-14 flex items-center justify-between px-4 border-b border-surface-800/50 bg-surface-900/50 backdrop-blur-xl z-50 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-trace-500 to-purple-600 flex items-center justify-center shadow-lg shadow-trace-500/20">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white leading-tight">Trace</h1>
              <p className="text-[10px] text-surface-400 leading-tight">Transparent Support AI</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {user && (
            <span className="text-[10px] text-surface-500 mr-1">{user.username}</span>
          )}
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-surface-800 text-surface-400 hover:text-red-400 transition-colors"
            title="Sign out"
          >
            <LogOut size={15} />
          </button>
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium ${
            backendStatus === 'online'
              ? 'bg-emerald-500/10 text-emerald-400'
              : backendStatus === 'offline'
              ? 'bg-red-500/10 text-red-400'
              : 'bg-amber-500/10 text-amber-400'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              backendStatus === 'online' ? 'bg-emerald-400' :
              backendStatus === 'offline' ? 'bg-red-400' : 'bg-amber-400'
            }`} />
            {backendStatus === 'online' ? 'API Online' :
             backendStatus === 'offline' ? 'API Offline' : 'Connecting...'}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 360, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="border-r border-surface-800/50 bg-surface-900/30 overflow-hidden shrink-0"
            >
              <div className="w-[360px] h-full">
                <KnowledgePanel />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <main className="flex-1 flex flex-col min-w-0 relative">
          {showWelcome ? (
            <WelcomeScreen onStart={handleStartChat} />
          ) : (
            <ChatWidget />
          )}
        </main>
      </div>
    </div>
  )
}
