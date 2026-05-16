import { useState, useEffect, useRef } from 'react'
import { Send, Settings, Loader2, AlertCircle } from 'lucide-react'
import ChatMessage from './components/ChatMessage'
import Sidebar from './components/Sidebar'
import { createSession, sendQuery } from './api'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showDebug, setShowDebug] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [error, setError] = useState(null)

  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Create session on mount
    createSession().then(id => setSessionId(id)).catch(err => {
      console.error("Failed to fetch session:", err)
      setError("Failed to connect to backend server. Make sure Python API is running.")
    })
  }, [])

  const handleReset = async () => {
    try {
      const newSessionId = await createSession()
      setSessionId(newSessionId)
      setMessages([])
      setError(null)
    } catch (err) {
      setError("Failed to create new session.")
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || !sessionId || isLoading) return

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    // Create a scaffold for the assistant's thinking message
    const assistantMessageId = Date.now().toString()
    const initialAssistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '', // Empty initially
      timestamp: new Date().toISOString(),
      isThinking: true,
      agentStatuses: [],
      result: null
    }

    setMessages(prev => [...prev, userMessage, initialAssistantMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      // Hardcoded 5 results for sleek design constraint per request
      const result = await sendQuery(sessionId, userMessage.content, 5, (event) => {
        if (event.type === 'agent_start') {
          setMessages(prev => prev.map(msg => {
            if (msg.id === assistantMessageId) {
              // Check if agent already exists in statuses
              const existingIndex = msg.agentStatuses.findIndex(s => s.agent === event.agent)
              
              if (existingIndex >= 0) {
                // Update existing agent status to running
                const updatedStatuses = [...msg.agentStatuses]
                updatedStatuses[existingIndex] = {
                  ...updatedStatuses[existingIndex],
                  status: 'running',
                  message: event.status
                }
                return {
                  ...msg,
                  agentStatuses: updatedStatuses
                }
              } else {
                // Add new agent status
                return {
                  ...msg,
                  agentStatuses: [
                    ...msg.agentStatuses,
                    { agent: event.agent, status: 'running', message: event.status }
                  ]
                }
              }
            }
            return msg
          }))
        } else if (event.type === 'agent_complete') {
          let spellcheckData = null
          if (event.agent === 'clarity' && event.output && event.output.spellcheck) {
            spellcheckData = event.output.spellcheck
          }

          setMessages(prev => prev.map(msg => {
            if (msg.id === assistantMessageId) {
              const newMsg = {
                ...msg,
                agentStatuses: msg.agentStatuses.map(s =>
                  s.agent === event.agent
                    ? { ...s, status: 'complete', output: event.output }
                    : s
                )
              }
              if (spellcheckData) {
                newMsg.spellcheck = spellcheckData
              }
              return newMsg
            }
            return msg
          }))
        }
      })

      // Query completed
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId) {
          return {
            ...msg,
            content: result.final_answer || 'No valid response generated.',
            isThinking: false,
            result: result
          }
        }
        return msg
      }))

    } catch (err) {
      console.error('Query error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred connecting to the backend.')
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId) {
          return {
            ...msg,
            content: '❌ An error occurred while processing your request. Please try again.',
            isThinking: false,
            agentStatuses: msg.agentStatuses.map(s => 
              s.status === 'running' ? { ...s, status: 'error' } : s
            )
          }
        }
        return msg
      }))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen overflow-hidden flex bg-[#121212] text-gray-200 selection:bg-indigo-500/30 font-sans">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        showDebug={showDebug}
        setShowDebug={setShowDebug}
        onReset={handleReset}
      />

      <div className="flex-1 flex flex-col relative w-full overflow-hidden">
        {/* Header */}
        <header className="bg-[#171717]/80 backdrop-blur-md border-b border-[#303134] sticky top-0 z-10 w-full pl-0">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
            <div className="flex items-center space-x-3 lg:pl-0 pl-10">
              <div className="lg:hidden absolute left-4 z-20">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="p-2 hover:bg-[#303134] rounded-xl transition-colors"
                >
                  <Settings className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-100 to-gray-400 bg-clip-text text-transparent flex items-center">
                Velora Context
              </h1>
            </div>
            {sessionId && (
              <div className="text-[10px] font-mono text-gray-600 bg-[#202124] px-3 py-1 rounded-full border border-[#303134] hidden sm:block shadow-inner">
                SESSION {sessionId.split('-')[0].toUpperCase()}
              </div>
            )}
          </div>
        </header>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 w-full custom-scrollbar">
          <div className="max-w-4xl mx-auto w-full">
            {messages.length === 0 ? (
              <div className="text-center py-[10vh] animate-in fade-in duration-700">
                <div className="inline-flex items-center justify-center w-40 h-40 rounded-3xl mb-8 relative group">
                  <div className="absolute inset-0 bg-indigo-500/20 rounded-3xl blur-xl group-hover:bg-purple-500/30 transition-all duration-500"></div>
                  <img 
                    src="/velora.png" 
                    alt="Velora" 
                    className="w-36 h-36 z-10" 
                    style={{ 
                      imageRendering: '-webkit-optimize-contrast',
                      objectFit: 'contain'
                    }} 
                  />
                </div>
                <h2 className="text-3xl lg:text-4xl font-bold text-gray-100 mb-5 tracking-tight">
                  What company can I research for you?
                </h2>
                <p className="text-gray-400 text-sm md:text-base max-w-xl mx-auto leading-relaxed mb-12">
                  Velora agents will autonomously scour the web, fact-check the data, and compile it into a beautifully formatted business report.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto text-left">
                  {[
                    { title: 'Deep Intelligence', desc: 'Financials, leadership, and product lines' },
                    { title: 'Competitor Analysis', desc: 'Market positioning vs direct rivals' },
                    { title: 'Verified Accuracy', desc: 'Autonomous cross-referencing of sources' }
                  ].map((item, i) => (
                    <div key={i} className="bg-[#171717] border border-[#303134] rounded-2xl p-5 hover:border-[#4c4f53] hover:bg-[#202124] transition-all shadow-lg hover:shadow-xl">
                      <h3 className="font-semibold text-gray-200 mb-2">{item.title}</h3>
                      <p className="text-xs text-gray-500 leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6 pb-10">
                {messages.map((message, index) => (
                  <ChatMessage
                    key={message.id || index}
                    message={message}
                    showDebug={showDebug}
                  />
                ))}

                {error && !isLoading && (
                  <div className="bg-red-900/10 border border-red-800/30 rounded-2xl p-5 flex items-start space-x-4 max-w-4xl mx-auto mt-4">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-semibold text-red-400 tracking-wide text-sm">Connection Error</h3>
                      <p className="text-red-300/80 text-xs mt-1 leading-relaxed">{error}</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Input Area */}
        <div className="bg-[#171717]/95 backdrop-blur-md border-t border-[#303134] p-4 w-full">
          <div className="max-w-4xl mx-auto relative">
            <form onSubmit={handleSubmit} className="relative flex items-center shadow-lg">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message Velora..."
                disabled={isLoading}
                autoFocus
                className="w-full bg-[#202124] text-gray-200 border border-[#3c4043] rounded-2xl py-4 pl-5 pr-14 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-all placeholder-gray-500 text-sm md:text-base font-medium tracking-wide shadow-inner"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2 p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-500 disabled:opacity-30 disabled:hover:bg-indigo-600 transition-all shadow-md active:scale-95"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5 ml-0.5" />
                )}
              </button>
            </form>
            <div className="text-center mt-3">
              <span className="text-[10px] text-gray-500 font-medium tracking-wide">Responses generated by autonomous agents. Verify critical information.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
