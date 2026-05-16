import { Loader2, Check, X, AlertCircle } from 'lucide-react'

// Map agent names to CLI-style icons
const agentCliIcons = {
  clarity: '🔍',
  research: '📚',
  validator: '🛡️',
  synthesis: '🧠'
}

// Map agent names to display names
const agentDisplayNames = {
  clarity: 'Clarity Agent',
  research: 'Research Agent',
  validator: 'Validator Agent',
  synthesis: 'Synthesis Agent'
}

export default function AgentProgress({ statuses, showDebug }) {
  // Extract confidence score from statuses
  const getConfidenceScore = () => {
    const researchAgent = statuses.find(s => s.agent === 'research' && s.output)
    if (researchAgent?.output?.confidence_score) {
      return researchAgent.output.confidence_score
    }
    return null
  }

  const getCliStatusLine = (status) => {
    const icon = agentCliIcons[status.agent] || '⚙️'
    const nameStr = agentDisplayNames[status.agent] || `${status.agent.charAt(0).toUpperCase() + status.agent.slice(1)} Agent`
    
    let info = ''
    if (status.status === 'running') {
      info = status.message || 'running...'
    } else if (status.status === 'complete' && status.output) {
      if (status.agent === 'clarity') {
        const clarityStatus = status.output.clarity_status || 'clear'
        const company = status.output.detected_company || ''
        info = `${clarityStatus}${company ? ` — ${company}` : ''}`
      } else if (status.agent === 'research') {
        const conf = status.output.confidence_score || 0
        const sources = status.output.total_results || 0
        const attempts = status.output.search_attempt || 1
        const confEmoji = conf >= 8 ? '🟢' : conf >= 6 ? '🟡' : '🔴'
        info = `confidence ${conf}/10 ${confEmoji} | ${sources} sources | attempt ${attempts}`
      } else if (status.agent === 'validator') {
        info = status.output.validation_result || 'passed'
      } else if (status.agent === 'synthesis') {
        info = status.output.report_status || 'completed'
      }
    } else if (status.status === 'error') {
      info = 'error 🔴'
    }

    return { icon, nameStr, info, status: status.status }
  }

  const confidenceScore = getConfidenceScore()
  const allComplete = statuses.length > 0 && statuses.every(s => s.status === 'complete' || s.status === 'error')
  const hasErrors = statuses.some(s => s.status === 'error')

  return (
    <div className="bg-[#0a0a0a] rounded-lg shadow-2xl p-5 border border-[#303134] max-w-4xl mx-auto mb-6 w-full font-mono text-[#e5e7eb]">
      <div className="flex items-center space-x-3 mb-6 border-b border-[#303134] pb-4">
        {statuses.some(s => s.status === 'running') ? (
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
        ) : allComplete && !hasErrors ? (
          <Check className="w-5 h-5 text-green-400" />
        ) : hasErrors ? (
          <AlertCircle className="w-5 h-5 text-red-400" />
        ) : (
          <span className="text-indigo-400">──────────────────────────────</span>
        )}
        <span className="text-sm tracking-widest text-indigo-400 font-bold uppercase">Agent Execution Flow</span>
        <span className="flex-1 text-indigo-400 hidden sm:inline">──────────────────────────────</span>
      </div>

      <div className="space-y-6">
        {statuses.map((status, idx) => {
          const cliData = getCliStatusLine(status)
          const agentName = `${agentDisplayNames[status.agent] || status.agent} Output`

          return (
            <div key={`${status.agent}-${idx}`} className="flex flex-col text-sm relative">
              <div className="mb-2 font-bold text-gray-200 tracking-wide flex items-center gap-3">
                {/* Checkmark indicator */}
                <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full border-2 transition-all duration-300 ${
                  cliData.status === 'complete' 
                    ? 'bg-green-500/20 border-green-500 text-green-400 scale-100' 
                    : cliData.status === 'running'
                    ? 'bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse'
                    : cliData.status === 'error'
                    ? 'bg-red-500/20 border-red-500 text-red-400'
                    : 'bg-gray-500/20 border-gray-500 text-gray-400'
                }`}>
                  {cliData.status === 'complete' ? (
                    <Check className="w-4 h-4 animate-in zoom-in duration-300" />
                  ) : cliData.status === 'running' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : cliData.status === 'error' ? (
                    <X className="w-4 h-4" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                  )}
                </span>
                
                <span className="flex-1">{cliData.icon} {cliData.nameStr} → {cliData.info}</span>
              </div>

              {/* Show JSON in a CLI-like ASCII box if debug is enabled and running/complete */}
              {showDebug && status.output && (
                <div className="text-[#a8b2d1] ml-9 animate-in fade-in duration-300">
                  <div className="flex text-gray-500 mb-1 items-center">
                    <span>╭</span>
                    <span className="mx-1">{"─".repeat(40)}</span>
                    <span className="text-gray-300 font-semibold px-2">{agentName}</span>
                    <span className="flex-1 overflow-hidden">{"─".repeat(100)}</span>
                    <span>╮</span>
                  </div>

                  <div className="border-l border-r border-gray-600 px-4 py-2 bg-[#101114] overflow-x-auto custom-scrollbar text-[13px] leading-relaxed">
                    <pre className="m-0 string-break">
                      {JSON.stringify(status.output, null, 2)}
                    </pre>
                  </div>

                  <div className="flex text-gray-500 mt-1 overflow-hidden">
                    <span>╰</span>
                    <span>{"─".repeat(200)}</span>
                    <span className="absolute right-6 bg-[#0a0a0a] px-1">╯</span>
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {/* Confidence Level Display at the end */}
        {allComplete && !hasErrors && confidenceScore !== null && (
          <div className="mt-8 pt-6 border-t border-[#303134] animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/30 rounded-lg p-4 hover:border-indigo-500/50 transition-all">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center animate-pulse">
                  <span className="text-2xl">📊</span>
                </div>
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Final Confidence Level</div>
                  <div className="text-lg font-bold text-gray-200 mt-0.5">
                    {confidenceScore}/10 
                    <span className="ml-2 text-sm">
                      {confidenceScore >= 8 ? '🟢 High' : confidenceScore >= 6 ? '🟡 Medium' : '🔴 Low'}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Visual confidence bar */}
              <div className="hidden sm:flex items-center gap-2">
                <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ease-out ${
                      confidenceScore >= 8 ? 'bg-green-500' : 
                      confidenceScore >= 6 ? 'bg-yellow-500' : 
                      'bg-red-500'
                    }`}
                    style={{ width: `${confidenceScore * 10}%` }}
                  />
                </div>
                <span className="text-sm font-mono text-gray-400">{confidenceScore * 10}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
