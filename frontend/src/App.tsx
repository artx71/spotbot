import { useState, useEffect, useRef } from 'react'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import { sendMessage, getHistory, createHackathon, type Message } from './services/api'

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [hackathonData, setHackathonData] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const userId = 'default_user'

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadHistory = async () => {
    try {
      const data = await getHistory(userId)
      if (data.history && data.history.length > 0) {
        setMessages(data.history)
      } else {
        setMessages([{
          role: 'assistant',
          content: "Welcome to Spot, your AI-powered hackathon assistant! 👋\n\nI'm here to help you create your custom hackathon and landing page. Let's start by telling me about your hackathon idea - what theme or focus area are you interested in?"
        }])
      }
    } catch (error) {
      console.error('Error loading history:', error)
      setMessages([{
        role: 'assistant',
        content: "Welcome to Spot, your AI-powered hackathon assistant! 👋\n\nI'm here to help you create your custom hackathon and landing page. Let's start by telling me about your hackathon idea - what theme or focus area are you interested in?"
      }])
    }
  }

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return

    const userMessage: Message = { role: 'user', content: message }
    setMessages((prev: Message[]) => [...prev, userMessage])
    setLoading(true)

    try {
      const data = await sendMessage(message, userId)
      setMessages(data.history || [])
      if (data.hackathon_data) {
        setHackathonData(data.hackathon_data)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev: Message[]) => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleCreateHackathon = async () => {
    if (!hackathonData) {
      const createMessage = "I'm ready to create my hackathon. Please generate the hackathon configuration."
      await handleSendMessage(createMessage)
      return
    }

    try {
      const result = await createHackathon(hackathonData, userId)
      if (result.success) {
        setMessages((prev: Message[]) => [...prev, {
          role: 'assistant',
          content: `✅ Great! Your hackathon "${result.hackathon.title}" has been created!\n\n${result.message || 'You can now view and manage your hackathon from the dashboard.'}`
        }])
      }
    } catch (error) {
      console.error('Error creating hackathon:', error)
      setMessages((prev: Message[]) => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error creating your hackathon. Please try again or continue our conversation to refine the details.'
      }])
    }
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chat with Spot</h1>
            <p className="text-sm text-gray-600 mt-1">Welcome to Spot, your AI-powered hackathon assistant!</p>
            <p className="text-xs text-gray-500 mt-1">Start chatting to create your custom hackathon and landing page.</p>
          </div>
          {hackathonData && (
            <button
              onClick={handleCreateHackathon}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
            >
              Create
            </button>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 bg-gray-50">
        <div className="max-w-5xl mx-auto space-y-4">
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              role={msg.role}
              content={msg.content}
            />
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg px-4 py-3 shadow-sm">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-5xl mx-auto">
          <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  )
}

export default App
