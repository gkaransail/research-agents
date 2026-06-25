import { useEffect, useState } from 'react'
import { listWorkflows, deleteWorkflow } from '../api'

const STATUS_BADGE = {
  pending:   'bg-gray-800 text-gray-400',
  running:   'bg-blue-900/50 text-blue-300',
  completed: 'bg-emerald-900/50 text-emerald-300',
  failed:    'bg-red-900/50 text-red-300',
}
const STATUS_ICON = { pending: '⏳', running: '⚡', completed: '✅', failed: '❌' }
const TYPE_ICON = { dd: '🏢', research: '🔍' }

export default function WorkflowList({ onSelect, selectedId, refreshKey, filterType }) {
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listWorkflows()
      .then(setWorkflows)
      .finally(() => setLoading(false))
  }, [refreshKey])

  const filtered = filterType
    ? workflows.filter(w => (w.type || 'research') === filterType)
    : workflows

  async function handleDelete(e, wfId) {
    e.stopPropagation()
    if (!confirm('Delete this workflow?')) return
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

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-600">
        <div className="text-5xl mb-3">{filterType === 'dd' ? '🏢' : '🔬'}</div>
        <div className="text-sm text-center">
          {filterType === 'dd' ? 'No DD analyses yet.' : 'No research yet.'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {filtered.map(wf => (
        <div
          key={wf.id}
          onClick={() => onSelect(wf)}
          className={`group border rounded-xl p-4 cursor-pointer transition-all ${
            selectedId === wf.id
              ? 'bg-gray-800 border-gray-600'
              : 'bg-gray-900 hover:bg-gray-800 border-gray-800 hover:border-gray-600'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-xs">{TYPE_ICON[wf.type || 'research']}</span>
                <p className="text-sm font-medium text-white truncate">{wf.query}</p>
              </div>
              <p className="text-xs text-gray-600 font-mono">
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
