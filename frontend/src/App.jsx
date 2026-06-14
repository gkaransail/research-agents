import { useState, useEffect } from 'react'
import NewResearch from './components/NewResearch'
import WorkflowList from './components/WorkflowList'
import WorkflowDetail from './components/WorkflowDetail'
import { getAgents } from './api'

export default function App() {
  const [showNew, setShowNew] = useState(false)
  const [selectedWfId, setSelectedWfId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [agents, setAgents] = useState([])

  useEffect(() => {
    getAgents().then(d => setAgents(d.agents || [])).catch(() => {})
  }, [])

  function handleCreated(wf) {
    setShowNew(false)
    setRefreshKey(k => k + 1)
    setSelectedWfId(wf.id)
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Top nav */}
      <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center text-sm font-bold">R</div>
          <span className="font-semibold text-white text-sm">Research Agents</span>
          <span className="text-gray-600 text-sm hidden sm:block">— multi-agent research system</span>
        </div>
        <div className="flex items-center gap-4">
          {agents.length > 0 && (
            <div className="hidden md:flex items-center gap-1">
              {agents.map(a => (
                <span key={a} className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded-full">{a}</span>
              ))}
            </div>
          )}
          <button
            onClick={() => setShowNew(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors"
          >
            + New Research
          </button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-72 border-r border-gray-800 flex flex-col flex-shrink-0">
          <div className="p-4 flex items-center justify-between border-b border-gray-800">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Workflows</span>
            <button
              onClick={() => setRefreshKey(k => k + 1)}
              className="text-gray-600 hover:text-gray-400 text-xs"
              title="Refresh"
            >
              ↻
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <WorkflowList
              onSelect={id => setSelectedWfId(id)}
              refreshKey={refreshKey}
            />
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-y-auto p-6">
          {selectedWfId ? (
            <WorkflowDetail
              wfId={selectedWfId}
              onBack={() => setSelectedWfId(null)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-4">
              <div className="text-6xl">🧠</div>
              <div className="text-center">
                <p className="text-lg font-medium text-gray-400">Select a workflow or start new research</p>
                <p className="text-sm mt-1">Agents will search, read, analyze, and write a report in real time</p>
              </div>
              <div className="grid grid-cols-4 gap-3 mt-4 max-w-lg">
                {[
                  { icon: '🔍', label: 'Search', desc: 'DuckDuckGo' },
                  { icon: '📄', label: 'Read', desc: 'Jina AI' },
                  { icon: '🧠', label: 'Analyze', desc: 'Groq LLM' },
                  { icon: '✍️', label: 'Write', desc: '.md report' },
                ].map(step => (
                  <div key={step.label} className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
                    <div className="text-2xl mb-1">{step.icon}</div>
                    <div className="text-xs font-semibold text-gray-300">{step.label}</div>
                    <div className="text-xs text-gray-600">{step.desc}</div>
                  </div>
                ))}
              </div>
              <button
                onClick={() => setShowNew(true)}
                className="mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Start Research
              </button>
            </div>
          )}
        </main>
      </div>

      {showNew && (
        <NewResearch onCreated={handleCreated} onClose={() => setShowNew(false)} />
      )}
    </div>
  )
}
