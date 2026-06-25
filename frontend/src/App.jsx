import { useState, useEffect } from 'react'
import NewResearch from './components/NewResearch'
import NewDDAnalysis from './components/NewDDAnalysis'
import WorkflowList from './components/WorkflowList'
import WorkflowDetail from './components/WorkflowDetail'
import DDWorkflowDetail from './components/DDWorkflowDetail'
import { getAgents } from './api'

export default function App() {
  const [mode, setMode] = useState('research')
  const [showNew, setShowNew] = useState(false)
  const [selectedWf, setSelectedWf] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [agents, setAgents] = useState([])

  useEffect(() => {
    getAgents().then(d => setAgents(d.agents || [])).catch(() => {})
  }, [])

  function handleCreated(wf) {
    setShowNew(false)
    setRefreshKey(k => k + 1)
    setSelectedWf(wf)
  }

  const isDD = selectedWf?.type === 'dd'

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center text-sm font-bold">R</div>
          <span className="font-semibold text-white text-sm">Research Agents</span>
          <span className="text-gray-600 text-sm hidden sm:block">— AI due diligence + research</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-gray-700 overflow-hidden text-sm">
            <button
              onClick={() => { setMode('research'); setSelectedWf(null) }}
              className={`px-3 py-1.5 transition-colors ${mode === 'research' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              Research
            </button>
            <button
              onClick={() => { setMode('dd'); setSelectedWf(null) }}
              className={`px-3 py-1.5 transition-colors ${mode === 'dd' ? 'bg-amber-600 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              Due Diligence
            </button>
          </div>
          <button
            onClick={() => setShowNew(true)}
            className={`text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors ${
              mode === 'dd' ? 'bg-amber-600 hover:bg-amber-500' : 'bg-indigo-600 hover:bg-indigo-500'
            }`}
          >
            + {mode === 'dd' ? 'New DD' : 'New Research'}
          </button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        <aside className="w-72 border-r border-gray-800 flex flex-col flex-shrink-0">
          <div className="p-4 flex items-center justify-between border-b border-gray-800">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {mode === 'dd' ? 'DD Analyses' : 'Workflows'}
            </span>
            <button onClick={() => setRefreshKey(k => k + 1)} className="text-gray-600 hover:text-gray-400 text-xs" title="Refresh">↻</button>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <WorkflowList
              filterType={mode}
              onSelect={wf => setSelectedWf(wf)}
              selectedId={selectedWf?.id}
              refreshKey={refreshKey}
            />
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          {selectedWf ? (
            isDD ? (
              <DDWorkflowDetail wfId={selectedWf.id} onBack={() => setSelectedWf(null)} />
            ) : (
              <WorkflowDetail wfId={selectedWf.id} onBack={() => setSelectedWf(null)} />
            )
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-4">
              {mode === 'dd' ? (
                <>
                  <div className="text-6xl">🏢</div>
                  <div className="text-center">
                    <p className="text-lg font-medium text-gray-400">AI-powered asset due diligence</p>
                    <p className="text-sm mt-1">Three specialist agents research valuation, regulatory, and risk in parallel</p>
                  </div>
                  <div className="grid grid-cols-4 gap-3 mt-4 max-w-lg">
                    {[
                      { icon: '💰', label: 'Valuation', desc: 'Market comps' },
                      { icon: '⚖️', label: 'Regulatory', desc: 'Compliance' },
                      { icon: '⚠️', label: 'Risk', desc: 'Risk profile' },
                      { icon: '📋', label: 'DD Report', desc: 'Score + params' },
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
                    className="mt-2 bg-amber-600 hover:bg-amber-500 text-white font-medium px-6 py-2 rounded-lg transition-colors"
                  >
                    Start Due Diligence
                  </button>
                </>
              ) : (
                <>
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
                </>
              )}
            </div>
          )}
        </main>
      </div>

      {showNew && mode === 'research' && (
        <NewResearch onCreated={handleCreated} onClose={() => setShowNew(false)} />
      )}
      {showNew && mode === 'dd' && (
        <NewDDAnalysis onCreated={handleCreated} onClose={() => setShowNew(false)} />
      )}
    </div>
  )
}
