import { useEffect, useState } from 'react'
import { getWorkflow } from '../api'
import { useWorkflow } from '../hooks/useWorkflow'
import AgentTimeline from './AgentTimeline'
import OutputViewer from './OutputViewer'

const STATUS_BADGE = {
  pending:   'bg-gray-800 text-gray-400 border-gray-600',
  running:   'bg-blue-900/40 text-blue-300 border-blue-600 animate-pulse',
  completed: 'bg-emerald-900/40 text-emerald-300 border-emerald-600',
  failed:    'bg-red-900/40 text-red-300 border-red-600',
}

const STATUS_ICON = {
  pending: '⏳', running: '⚡', completed: '✅', failed: '❌',
}

export default function WorkflowDetail({ wfId, onBack }) {
  const [meta, setMeta] = useState(null)
  const { events, status, outputFile } = useWorkflow(wfId)

  useEffect(() => {
    if (!wfId) return
    getWorkflow(wfId).then(wf => {
      setMeta(wf)
    })
  }, [wfId])

  const currentStatus = status || meta?.status || 'pending'
  const currentOutput = outputFile || meta?.output_file

  const agentNames = [...new Set(events.map(e => e.agent_name))]

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <button
          onClick={onBack}
          className="text-gray-500 hover:text-gray-300 mt-1 flex-shrink-0"
        >
          ← Back
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <span className={`text-xs font-mono px-2 py-0.5 rounded border ${STATUS_BADGE[currentStatus]}`}>
              {STATUS_ICON[currentStatus]} {currentStatus}
            </span>
            {agentNames.map(name => (
              <span key={name} className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded">
                {name}
              </span>
            ))}
          </div>
          <h2 className="text-lg font-semibold text-white leading-snug">{meta?.query || '...'}</h2>
          {meta?.created_at && (
            <p className="text-xs text-gray-600 mt-1 font-mono">
              Started {new Date(meta.created_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {currentStatus === 'running' && (
        <div className="mb-4 h-1 bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full bg-indigo-500 rounded-full animate-[progress_2s_ease-in-out_infinite]"
            style={{ width: `${Math.min(90, (events.length / 20) * 100)}%`, transition: 'width 0.5s ease' }}
          />
        </div>
      )}

      {/* Agent activity */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Agent Activity · {events.length} events
        </h3>
        <AgentTimeline events={events} status={currentStatus} />
      </div>

      {/* Report output */}
      {currentStatus === 'completed' && currentOutput && (
        <OutputViewer outputFile={currentOutput} />
      )}

      {currentStatus === 'failed' && (
        <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
          Research failed. Check the agent activity above for details, then verify your GROQ_API_KEY is valid.
        </div>
      )}
    </div>
  )
}
