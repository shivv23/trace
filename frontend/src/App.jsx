import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Menu, X, MessageSquare, FileText, BarChart3, LogOut, Plus, Trash2, Clock, ChevronRight, Users, BookOpen, MessageCircle, Activity } from 'lucide-react'
import ChatWidget from './components/ChatWidget'
import WelcomeScreen from './components/WelcomeScreen'
import LoginScreen from './components/LoginScreen'
import { healthCheck, getStoredUser, isAuthenticated, logout, listConversations, deleteConversation, getAdminStats } from './utils/api'

export default function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showWelcome, setShowWelcome] = useState(true)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [user, setUser] = useState(null)
  const [conversations, setConversations] = useState([])
  const [activeConvId, setActiveConvId] = useState(null)
  const [sidebarTab, setSidebarTab] = useState('chats')
  const [adminStats, setAdminStats] = useState(null)

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
    loadConversations()
    if (user?.isAdmin) loadAdminStats()
  }, [authenticated])

  const loadConversations = async () => {
    try {
      const data = await listConversations()
      setConversations(data.conversations || [])
    } catch {}
  }

  const loadAdminStats = async () => {
    try {
      const data = await getAdminStats()
      setAdminStats(data)
    } catch {}
  }

  const handleLogin = () => {
    setAuthenticated(true)
    setUser(getStoredUser())
  }

  const handleLogout = () => {
    logout()
    setAuthenticated(false)
    setUser(null)
    setShowWelcome(true)
    setConversations([])
  }

  const handleStartChat = () => setShowWelcome(false)

  const handleNewChat = () => {
    setActiveConvId(null)
    setShowWelcome(true)
    window.dispatchEvent(new CustomEvent('trace-new-chat'))
  }

  const handleSelectConversation = (convId) => {
    setActiveConvId(convId)
    setShowWelcome(false)
    window.dispatchEvent(new CustomEvent('trace-load-conversation', { detail: { conversationId: convId } }))
  }

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation()
    try {
      await deleteConversation(convId)
      setConversations(prev => prev.filter(c => c.id !== convId))
      if (activeConvId === convId) handleNewChat()
    } catch {}
  }

  const handleConversationSaved = () => {
    loadConversations()
  }

  useEffect(() => {
    const handler = () => loadConversations()
    window.addEventListener('trace-conversation-saved', handler)
    return () => window.removeEventListener('trace-conversation-saved', handler)
  }, [])

  const formatDate = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now - d
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return 'Just now'
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHr = Math.floor(diffMin / 60)
    if (diffHr < 24) return `${diffHr}h ago`
    return d.toLocaleDateString()
  }

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
            <span className="text-[10px] text-surface-500 mr-1">{user.username}{user.isAdmin ? ' (Admin)' : ''}</span>
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
              animate={{ width: 340, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="border-r border-surface-800/50 bg-surface-900/30 overflow-hidden shrink-0 flex flex-col"
            >
              <div className="w-[340px] h-full flex flex-col">
                <div className="flex border-b border-surface-800/50 shrink-0">
                  <button
                    onClick={() => setSidebarTab('chats')}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                      sidebarTab === 'chats' ? 'text-trace-400 border-b-2 border-trace-500' : 'text-surface-500 hover:text-surface-300'
                    }`}
                  >
                    <MessageSquare size={14} />
                    Chats
                  </button>
                  <button
                    onClick={() => setSidebarTab('files')}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                      sidebarTab === 'files' ? 'text-trace-400 border-b-2 border-trace-500' : 'text-surface-500 hover:text-surface-300'
                    }`}
                  >
                    <FileText size={14} />
                    Files
                  </button>
                  {user?.isAdmin && (
                    <button
                      onClick={() => setSidebarTab('admin')}
                      className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                        sidebarTab === 'admin' ? 'text-trace-400 border-b-2 border-trace-500' : 'text-surface-500 hover:text-surface-300'
                      }`}
                    >
                      <BarChart3 size={14} />
                      Stats
                    </button>
                  )}
                </div>

                <div className="flex-1 overflow-y-auto scrollbar-hide">
                  {sidebarTab === 'chats' && (
                    <div className="p-3 space-y-1">
                      <button
                        onClick={handleNewChat}
                        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-medium
                          bg-trace-500/10 text-trace-400 hover:bg-trace-500/20 border border-trace-500/20
                          transition-all duration-200 mb-2"
                      >
                        <Plus size={14} />
                        New Conversation
                      </button>
                      {conversations.length === 0 && (
                        <p className="text-xs text-surface-500 text-center py-8">No conversations yet</p>
                      )}
                      {conversations.map((conv) => (
                        <motion.button
                          key={conv.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          onClick={() => handleSelectConversation(conv.id)}
                          className={`w-full flex items-start gap-2.5 px-3 py-2.5 rounded-lg text-left transition-all duration-200 group ${
                            activeConvId === conv.id
                              ? 'bg-trace-500/10 border border-trace-500/20'
                              : 'hover:bg-surface-800/50 border border-transparent'
                          }`}
                        >
                          <MessageSquare size={14} className="mt-0.5 shrink-0 text-surface-500" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-surface-300 truncate">
                              {conv.message_count > 0 ? `${conv.message_count} messages` : 'Empty chat'}
                            </p>
                            <div className="flex items-center gap-1.5 mt-1">
                              <Clock size={10} className="text-surface-600" />
                              <span className="text-[10px] text-surface-600">{formatDate(conv.updated_at)}</span>
                            </div>
                          </div>
                          <button
                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                            className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-surface-500 hover:text-red-400 transition-all"
                          >
                            <Trash2 size={12} />
                          </button>
                        </motion.button>
                      ))}
                    </div>
                  )}

                  {sidebarTab === 'files' && (
                    <div className="p-3 overflow-y-auto h-full">
                      <KnowledgePanelContent />
                    </div>
                  )}

                  {sidebarTab === 'admin' && adminStats && (
                    <div className="p-4 space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <StatCard icon={<Users size={16} />} label="Users" value={adminStats.users} />
                        <StatCard icon={<BookOpen size={16} />} label="Documents" value={adminStats.documents} />
                        <StatCard icon={<MessageCircle size={16} />} label="Conversations" value={adminStats.conversations} />
                        <StatCard icon={<Activity size={16} />} label="Messages" value={adminStats.messages} />
                      </div>
                      <div className="glass-panel rounded-xl px-4 py-3">
                        <p className="text-[10px] text-surface-500 uppercase tracking-wider">Output Volume</p>
                        <p className="text-lg font-semibold text-white mt-1">
                          {adminStats.total_output_chars > 1000000
                            ? `${(adminStats.total_output_chars / 1000000).toFixed(1)}M`
                            : adminStats.total_output_chars > 1000
                            ? `${(adminStats.total_output_chars / 1000).toFixed(1)}K`
                            : adminStats.total_output_chars} chars
                        </p>
                        <p className="text-[10px] text-surface-600 mt-1">{adminStats.feedback_entries} feedback entries</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <main className="flex-1 flex flex-col min-w-0 relative">
          {showWelcome ? (
            <WelcomeScreen onStart={handleStartChat} />
          ) : (
            <ChatWidget key={activeConvId || 'new'} conversationId={activeConvId} onConversationSaved={handleConversationSaved} />
          )}
        </main>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value }) {
  return (
    <div className="glass-panel rounded-xl px-3 py-3">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-surface-400">{icon}</span>
        <span className="text-[10px] text-surface-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value ?? '—'}</p>
    </div>
  )
}

function KnowledgePanelContent() {
  const [docs, setDocs] = useState([])
  useEffect(() => {
    import('./utils/api').then(({ listDocuments }) => {
      listDocuments().then(setDocs).catch(() => {})
    })
  }, [])
  if (docs.length === 0) {
    return <p className="text-xs text-surface-500 text-center py-8">No documents uploaded</p>
  }
  return (
    <div className="space-y-2">
      {docs.map((doc) => (
        <div key={doc.id} className="glass-panel rounded-xl px-3 py-2.5">
          <p className="text-xs text-surface-300 truncate">{doc.name}</p>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[10px] text-surface-600">{doc.type}</span>
            <span className="text-[10px] text-surface-600">{doc.chunk_count} chunks</span>
            <span className="text-[10px] text-surface-600">{Math.round(doc.size_bytes / 1024)}KB</span>
          </div>
        </div>
      ))}
    </div>
  )
}
