import { useState, useCallback, useRef } from 'react'
import { sendMessage, submitFeedback } from '../utils/api'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [error, setError] = useState(null)
  const assistantIndex = useRef(-1)

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
  }, [])

  return { messages, isLoading, error, send, rateMessage, clear }
}
