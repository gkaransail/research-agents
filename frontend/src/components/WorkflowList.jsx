import { useEffect, useState } from 'react'
import { listWorkflows, deleteWorkflow } from '../api'

const STATUS_BADGE = {
  pending:   'bg-gray-800 text-gray-400',
  running:   'bg-blue-900/50 text-blue-300',
  completed: 'bg-emerald-900/50 text-emerald-300',
  failed:    'bg-red-900/50 text-red-300',
}

const STATUS_ICON = {
  pending: '⏳', running: '⚡', completed: '✅', failed: '❌',
}

export default function WorkflowList({ onSelect, refreshKey }) {
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listWorkflows()
      .then(setWorkflows)
      .finally(() => setLoading(false))
  }, [refreshKey])

  async function handleDelete(e, wfId) {
    e.stopPropagation()
    if (!confirm('Delete this research workflow?')) return
    await deleteWorkflow(wfId)
    setWorkflows(prev => prev.filter(w => w.id !== wfId))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-600">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (workflows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-600">
        <div className="text-5xl mb-3">🔬</div>
        <div className="text-sm">No research yet. Start your first query!</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {workflows.map(wf => (
        <div
          key={wf.id}
          onClick={() => onSelect(wf.id)}
          className="group bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-600 rounded-xl p-4 cursor-pointer transition-all"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{wf.query}</p>
              <p className="text-xs text-gray-600 mt-1 font-mono">
                {new Date(wf.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${STATUS_BADGE[wf.status]}`}>
                {STATUS_ICON[wf.status]} {wf.status}
              </span>
              <button
                onClick={e => handleDelete(e, wf.id)}
                className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all text-xs px-1"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
