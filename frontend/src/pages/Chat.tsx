import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import ChatInput from '../components/ChatInput'
import ChatWindow from '../components/ChatWindow'
import type { ChatState, Message } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const STORAGE_KEY = 'dualmind_chat_state'

const createMessage = (
  sender: Message['sender'],
  content: string,
  attachments?: Message['attachments'],
): Message => ({
  id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  sender,
  content,
  attachments,
  createdAt: new Date().toISOString(),
})

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return
    try {
      const parsed: ChatState = JSON.parse(stored)
      setMessages(parsed.messages || [])
      setSessionId(parsed.sessionId)
    } catch (error) {
      console.error('Failed to parse stored chat state', error)
    }
  }, [])

  useEffect(() => {
    const state: ChatState = {
      messages,
      sessionId,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [messages, sessionId])

  const client = useMemo(() => {
    const instance = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return instance
  }, [])

  const handleSend = useCallback(async ({ text, file }: { text: string; file?: File }) => {
    const attachments = file
      ? [
          {
            filename: file.name,
            size: file.size,
            contentType: file.type,
          },
        ]
      : undefined

    const userMessage = createMessage('user', text || (file ? `Uploaded ${file.name}` : ''), attachments)
    setMessages((prev) => [...prev, userMessage])

    setIsTyping(true)

    try {
      if (file) {
        const formData = new FormData()
        formData.append('file', file)
        if (text) {
          formData.append('message', text)
        }

        const uploadResponse = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        if (uploadResponse.data?.session_id) {
          setSessionId(uploadResponse.data.session_id)
        }

        if (uploadResponse.data?.response) {
          setMessages((prev) => [...prev, createMessage('assistant', uploadResponse.data.response)])
        } else {
          setMessages((prev) => [
            ...prev,
            createMessage(
              'assistant',
              text
                ? 'Your file has been processed. Let me know if you need anything else.'
                : 'Your file is uploaded. Ask a question to get insights.',
            ),
          ])
        }
      } else {
        const chatResponse = await client.post('/api/chat', { message: text })
        setMessages((prev) => [...prev, createMessage('assistant', chatResponse.data.response)])
        setSessionId(chatResponse.data.session_id)
      }
    } catch (error) {
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : 'Unexpected error occurred.'
      setMessages((prev) => [...prev, createMessage('assistant', `Sorry, I ran into an issue: ${detail}`)])
    } finally {
      setIsTyping(false)
    }
  }, [client])

  const clearChat = () => {
    if (!window.confirm('Clear conversation history?')) return
    setMessages([])
    setSessionId(undefined)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-dark-bg border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 
                     bg-clip-text text-transparent 
                     hover:opacity-90 transition-all duration-200"
          >
            DualMind
          </Link>
          <button
            type="button"
            onClick={clearChat}
            className="px-4 py-2 rounded-lg border border-aqua text-aqua bg-transparent text-sm font-medium transition-all duration-200 ease-in-out hover:bg-aqua-hover"
          >
            Clear Chat
          </button>
        </div>
      </header>

      {/* Chat Window */}
      <ChatWindow messages={messages} isTyping={isTyping} />

      {/* Input Bar */}
      <ChatInput onSend={handleSend} disabled={isTyping} />
    </div>
  )
}

export default Chat
