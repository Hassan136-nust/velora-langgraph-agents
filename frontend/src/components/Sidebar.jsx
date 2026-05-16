import { X, Trash2, Settings } from 'lucide-react'

export default function Sidebar({
  isOpen,
  onClose,
  showDebug,
  setShowDebug,
  onReset
}) {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-80 bg-[#171717] text-gray-200 border-r border-[#303134] transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-[#303134]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <img 
                  src="/velora.png" 
                  alt="Velora" 
                  className="w-17 h-10" 
                  style={{ 
                    imageRendering: '-webkit-optimize-contrast',
                    objectFit: 'contain'
                  }} 
                />
                
              </div>
              <button
                onClick={onClose}
                className="lg:hidden p-2 hover:bg-[#303134] rounded-lg transition-colors"
                aria-label="Close sidebar"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <p className="text-sm text-gray-400">Premium Business Intelligence</p>
          </div>

          {/* Settings */}
          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4 flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>Preferences</span>
              </h3>

              {/* Debug Toggle */}
              <div className="bg-[#202124] p-4 rounded-xl border border-[#303134]">
                <label className="flex items-center justify-between cursor-pointer group">
                  <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">Developer Mode</span>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={showDebug}
                      onChange={(e) => setShowDebug(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-[#3c4043] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500"></div>
                  </div>
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  Display agent rationale, JSON outputs, and raw pipeline logs.
                </p>
              </div>
            </div>

            {/* Info Section */}
            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Pipeline Status</h3>
              <div className="bg-[#202124] rounded-xl p-4 border border-[#303134]">
                <ul className="text-sm text-gray-400 space-y-3">
                  <li className="flex items-start space-x-3">
                    <div className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shadow-[0_0_8px_rgba(34,211,238,0.6)]"></div>
                    <span><strong className="text-gray-200">Clarity</strong> validates format</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shadow-[0_0_8px_rgba(96,165,250,0.6)]"></div>
                    <span><strong className="text-gray-200">Research</strong> scrapes data</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-2 h-2 rounded-full bg-yellow-400 mt-1.5 shadow-[0_0_8px_rgba(250,204,21,0.6)]"></div>
                    <span><strong className="text-gray-200">Validator</strong> asserts quality</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-2 h-2 rounded-full bg-purple-400 mt-1.5 shadow-[0_0_8px_rgba(192,132,252,0.6)]"></div>
                    <span><strong className="text-gray-200">Synthesis</strong> maps the report</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-6 border-t border-[#303134] bg-[#171717]">
            <button
              onClick={onReset}
              className="w-full px-4 py-3 bg-[#303134] hover:bg-[#3c4043] text-gray-200 rounded-xl transition-all flex items-center justify-center space-x-2 font-medium"
            >
              <Trash2 className="w-4 h-4 text-red-400" />
              <span>Clear Session</span>
            </button>
            <p className="text-[11px] text-gray-500 text-center mt-5 font-medium tracking-wide">
              POWERED BY LANGGRAPH
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}
