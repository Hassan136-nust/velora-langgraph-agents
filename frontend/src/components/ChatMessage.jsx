import { User, Bot, ExternalLink, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AgentProgress from './AgentProgress'

export default function ChatMessage({ message, showDebug }) {
  const [showSources, setShowSources] = useState(false)
  const [showAgentOutputs, setShowAgentOutputs] = useState(false)
  const [showLogs, setShowLogs] = useState(false)

  const isUser = message.role === 'user'
  const result = message.result

  const getConfidenceBadge = (score) => {
    if (score >= 8) {
      return (
        <div className="inline-flex items-center space-x-1 px-3 py-1 bg-green-500/10 border border-green-500/20 text-green-400 rounded-full text-xs font-semibold tracking-wide">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>CONFIDENCE {score}/10</span>
        </div>
      )
    } else if (score >= 6) {
      return (
        <div className="inline-flex items-center space-x-1 px-3 py-1 bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 rounded-full text-xs font-semibold tracking-wide">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>CONFIDENCE {score}/10</span>
        </div>
      )
    } else {
      return (
        <div className="inline-flex items-center space-x-1 px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-400 rounded-full text-xs font-semibold tracking-wide">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>CONFIDENCE {score}/10</span>
        </div>
      )
    }
  }

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex space-x-4 max-w-4xl w-full ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>

        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg border ${isUser
            ? 'bg-[#171717] border-[#303134]'
            : 'bg-gradient-to-br from-indigo-500 to-purple-600 border-transparent relative z-10'
          }`}>
          {isUser ? (
            <User className="w-5 h-5 text-gray-300" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 min-w-0 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>

          {/* CLI-Style Early Spellcheck Banner */}
          {!isUser && (message.spellcheck || (result && result.spellcheck_result)) && (() => {
            const spellcheck = message.spellcheck || result.spellcheck_result
            if (!spellcheck || spellcheck.status === 'no_correction') return null

            return (
              <div className="w-full mb-5 ml-1 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className={`p-3 rounded-md border ${
                    spellcheck.status === 'corrected'
                      ? 'border-green-400/80 bg-green-500/10'
                      : 'border-yellow-400/80 bg-yellow-500/10'
                  } font-mono text-sm max-w-4xl flex items-center shadow-md`}>
                  <div className={`${
                    spellcheck.status === 'corrected' ? 'bg-green-500' : 'bg-yellow-500'
                  } text-white rounded text-[11px] font-bold px-1.5 py-0.5 mr-3 flex-shrink-0 tracking-widest`}>
                    {spellcheck.status === 'corrected' ? '✓' : '?'}
                  </div>
                  <div className="tracking-wide flex-1 break-words">
                    {spellcheck.status === 'corrected' ? (
                      <>
                        <span className="text-green-400 font-bold mr-2">🔤 Auto-corrected:</span>
                        <span className="text-gray-300">"{spellcheck.original}"</span>
                        <span className="text-gray-500 mx-2">→</span>
                        <span className="text-green-400 font-bold">{spellcheck.suggested}</span>
                        {spellcheck.confidence && (
                          <span className="text-gray-500 ml-2">
                            (confidence: {Math.round(spellcheck.confidence * 100)}%)
                          </span>
                        )}
                      </>
                    ) : (
                      <>
                        <span className="text-yellow-400 font-bold mr-2">🤔 Did you mean:</span>
                        <span className="text-yellow-400 font-bold">{spellcheck.suggested}</span>
                        <span className="text-gray-500 ml-2">instead of "{spellcheck.original}"?</span>
                        {spellcheck.confidence && (
                          <span className="text-gray-500 ml-2">
                            ({Math.round(spellcheck.confidence * 100)}% match)
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Agent Pipeline Progress History */}
          {!isUser && message.agentStatuses && message.agentStatuses.length > 0 && (
            <div className="w-full mb-3 ml-1">
              <AgentProgress statuses={message.agentStatuses} showDebug={showDebug} />
            </div>
          )}

          <div className={`w-full rounded-2xl shadow-md border ${isUser
              ? 'px-5 py-4 bg-[#28292c] border-[#3c4043] text-gray-200'
              : 'px-6 py-6 md:px-8 bg-[#202124] border-[#303134] text-gray-200 relative overflow-hidden'
            }`}>

            {/* Thinking Animation */}
            {message.isThinking && (
              <div className="absolute top-0 left-0 w-full h-1 bg-indigo-500/20 overflow-hidden">
                <div className="w-1/3 h-full bg-indigo-500 absolute animate-[slide_1.5s_ease-in-out_infinite]"></div>
              </div>
            )}

            {isUser ? (
              <p className="text-gray-200 text-sm md:text-base leading-relaxed break-words">{message.content}</p>
            ) : message.isThinking ? (
              <div className="flex items-center space-x-3 text-indigo-400 font-medium tracking-wide animate-pulse py-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Velora is synthesizing data...</span>
              </div>
            ) : (
              <div className="markdown-container overflow-x-auto w-full">
                <div className="prose prose-invert prose-indigo max-w-none text-[14px] leading-[1.7]">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>

          {/* Assistant Extras Container (Sources, Badges, Debug) */}
          {!isUser && result && !message.isThinking && (
            <div className="mt-4 space-y-3 w-full pl-2">

              {/* Confidence badge */}
              {result.confidence_score !== undefined && result.confidence_score > 0 && (
                <div className="flex items-center space-x-3 mb-2">
                  {getConfidenceBadge(result.confidence_score)}
                  {result.attempts !== undefined && result.attempts > 1 && (
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-widest">
                      {result.attempts} ATTEMPTS
                    </span>
                  )}
                </div>
              )}

              {/* Sources Accordion */}
              {result.research_findings && result.research_findings.items && result.research_findings.items.length > 0 && (
                <div className="bg-[#171717]/80 rounded-xl border border-[#303134] overflow-hidden">
                  <button
                    onClick={() => setShowSources(!showSources)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#202124] transition-colors"
                  >
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
                      <ExternalLink className="w-4 h-4 text-indigo-400" />
                      <span>Cited Sources ({result.research_findings.items.length})</span>
                    </span>
                    {showSources ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  {showSources && (
                    <div className="p-3 space-y-2 border-t border-[#303134] bg-[#121212]">
                      {result.research_findings.items.map((item, idx) => (
                        <a
                          key={idx}
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block p-4 bg-[#202124] rounded-lg hover:border-gray-500 transition-all border border-[#303134] group"
                        >
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-200 mb-1.5 group-hover:text-indigo-300 transition-colors line-clamp-1">{item.title}</h4>
                            <p className="text-[12px] text-gray-500 line-clamp-2 leading-relaxed">{item.content || item.snippet}</p>
                            <p className="text-[10px] font-medium text-indigo-400 mt-2.5 flex items-center space-x-1.5 opacity-80 group-hover:opacity-100 uppercase tracking-widest pl-0.5">
                              <ExternalLink className="w-3 h-3" />
                              <span>{new URL(item.url).hostname}</span>
                            </p>
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Debug: Agent Outputs */}
              {showDebug && result.agent_outputs && Object.keys(result.agent_outputs).length > 0 && (
                <div className="bg-[#171717]/80 rounded-xl border border-[#303134] overflow-hidden mt-6">
                  <button
                    onClick={() => setShowAgentOutputs(!showAgentOutputs)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#202124] transition-colors"
                  >
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center">
                      <span className="mr-2 text-cyan-500 font-mono">{"{ }"}</span> Agent JSON Payloads
                    </span>
                    {showAgentOutputs ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  {showAgentOutputs && (
                    <div className="p-3 space-y-3 border-t border-[#303134] max-h-96 overflow-y-auto custom-scrollbar bg-[#121212]">
                      {Object.entries(result.agent_outputs).map(([agent, output]) => (
                        <div key={agent} className="bg-[#202124] rounded-lg p-3 border border-[#303134]">
                          <h4 className="font-semibold text-[10px] tracking-widest uppercase text-gray-400 mb-2 border-b border-[#303134] pb-2">{agent}</h4>
                          <pre className="text-[11px] text-gray-300 overflow-x-auto string-break font-mono bg-[#171717] p-3 rounded border border-[#303134]">
                            {JSON.stringify(output, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Debug: Pipeline Logs */}
              {showDebug && result.agent_logs && result.agent_logs.length > 0 && (
                <div className="bg-[#171717]/80 rounded-xl border border-[#303134] overflow-hidden">
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#202124] transition-colors"
                  >
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center">
                      <span className="mr-2 text-yellow-500 font-mono">≡</span> Pipeline Execution Logs
                    </span>
                    {showLogs ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  {showLogs && (
                    <div className="p-3 space-y-1.5 border-t border-[#303134] max-h-64 overflow-y-auto custom-scrollbar bg-[#121212]">
                      {result.agent_logs.map((log, idx) => {
                        const levelColors = {
                          INFO: 'text-green-400',
                          WARNING: 'text-yellow-400',
                          ERROR: 'text-red-400',
                          DEBUG: 'text-gray-500'
                        }
                        return (
                          <div key={idx} className="text-[10px] font-mono bg-[#202124] p-2 rounded-md border border-[#303134] flex items-start">
                            <span className={`w-16 flex-shrink-0 font-bold ${levelColors[log.level]}`}>[{log.level}]</span>
                            <span className="w-32 flex-shrink-0 text-cyan-400/80 uppercase tracking-wider">{log.agent}</span>
                            <span className="text-gray-400 flex-1 break-words">{log.message}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <span className="text-[10px] text-gray-500 mt-2 px-1 font-medium select-none uppercase tracking-widest pl-2">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  )
}
