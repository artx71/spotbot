interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">
          {content}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
