import { useState, useCallback, useRef } from 'react'
import { sendMessage, submitFeedback, getConversationHistory } from '../utils/api'

function getToken() {
  return localStorage.getItem('trace_token')
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [error, setError] = useState(null)
  const assistantIndex = useRef(-1)
  const activeConvId = useRef(null)

  const loadConversation = useCallback(async (convId) => {
    setIsLoading(true)
    setError(null)
    activeConvId.current = convId
    try {
      const data = await getConversationHistory(convId)
      setConversationId(data.conversation_id)
      let aiIdx = -1
      const loaded = (data.messages || []).map((msg, idx) => {
        const isAssistant = msg.role === 'assistant'
        if (isAssistant) aiIdx += 1
        return {
          id: `msg-${msg.id || idx}`,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          confidence: msg.confidence,
          conversationId: data.conversation_id,
          messageIndex: isAssistant ? aiIdx : undefined,
          timestamp: msg.created_at,
        }
      })
      assistantIndex.current = aiIdx
      setMessages(loaded)
    } catch (err) {
      setError(err?.message || 'Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const send = useCallback(async (text) => {
    setIsLoading(true)
    setError(null)

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])

    const tempId = (Date.now() + 1).toString()
    const assistantMessage = {
      id: tempId,
      role: 'assistant',
      content: '',
      sources: [],
      confidence: null,
      conversationId: conversationId,
      messageIndex: assistantIndex.current + 1,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      const token = getToken()
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const body = JSON.stringify({
        message: text,
        conversation_id: conversationId || null,
        document_ids: null,
      })

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers,
        body,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Stream error' }))
        throw new Error(errData.detail || `Request failed: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullAnswer = ''
      let newConvId = conversationId

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (!data) continue

          try {
            const parsed = JSON.parse(data)

            if (parsed.type === 'token') {
              fullAnswer += parsed.text || ''
              setMessages(prev => prev.map(m =>
                m.id === tempId ? { ...m, content: fullAnswer } : m
              ))
            } else if (parsed.type === 'metadata') {
              newConvId = parsed.conversation_id
              if (!conversationId) {
                setConversationId(newConvId)
              }
              setMessages(prev => prev.map(m =>
                m.id === tempId
                  ? {
                      ...m,
                      sources: parsed.sources || [],
                      confidence: parsed.confidence || null,
                      conversationId: newConvId,
                      processingTime: parsed.processing_time_ms,
                      grounded: parsed.grounded,
                      suggestedQuestions: parsed.suggested_questions || [],
                    }
                  : m
              ))
            } else if (parsed.type === 'error') {
              setError(parsed.message || 'Stream error')
            }
          } catch {}
        }
      }

      assistantIndex.current += 1
    } catch (err) {
      setMessages(prev => prev.filter(m => m.id !== tempId))
      setError(err?.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }, [conversationId])

  const sendNonStreaming = useCallback(async (text) => {
    setIsLoading(true)
    setError(null)

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await sendMessage(text, conversationId)

      if (!conversationId) {
        setConversationId(response.conversation_id)
      }

      assistantIndex.current += 1

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        conversationId: response.conversation_id,
        messageIndex: assistantIndex.current,
        processingTime: response.processing_time_ms,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err?.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }, [conversationId])

  const rateMessage = useCallback(async (messageIndex, rating, correctedAnswer = null) => {
    if (!conversationId) return
    try {
      await submitFeedback(conversationId, messageIndex, rating, correctedAnswer)
      setMessages(prev => prev.map(m => {
        if (m.messageIndex === messageIndex && m.role === 'assistant') {
          return { ...m, rating }
        }
        return m
      }))
    } catch (err) {
      console.error('Feedback failed:', err)
    }
  }, [conversationId])

  const clear = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setError(null)
    assistantIndex.current = -1
    activeConvId.current = null
  }, [])

  return { messages, isLoading, error, send, rateMessage, clear, loadConversation }
}
