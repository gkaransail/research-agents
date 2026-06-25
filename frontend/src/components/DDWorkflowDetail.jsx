import { useEffect, useState } from 'react'
import { getWorkflow, tokenizeAsset } from '../api'
import { useWorkflow } from '../hooks/useWorkflow'
import AgentTimeline from './AgentTimeline'
import OutputViewer from './OutputViewer'

const STATUS_BADGE = {
  pending:   'bg-gray-800 text-gray-400 border-gray-600',
  running:   'bg-amber-900/40 text-amber-300 border-amber-600 animate-pulse',
  completed: 'bg-emerald-900/40 text-emerald-300 border-emerald-600',
  failed:    'bg-red-900/40 text-red-300 border-red-600',
}
const STATUS_ICON = { pending: '⏳', running: '⚡', completed: '✅', failed: '❌' }

const SCORE_COLOR = score =>
  score >= 70 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400'

const REC_BADGE = rec => {
  if (rec === 'PROCEED') return 'bg-emerald-900/40 text-emerald-300 border-emerald-600'
  if (rec === 'PROCEED WITH CAUTION') return 'bg-amber-900/40 text-amber-300 border-amber-600'
  return 'bg-red-900/40 text-red-300 border-red-600'
}

function TokenizePanel({ wfId }) {
  const [privateKey, setPrivateKey] = useState('')
  const [rpcUrl, setRpcUrl] = useState('http://127.0.0.1:8545')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function deploy() {
    if (!privateKey.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await tokenizeAsset(wfId, { private_key: privateKey.trim(), rpc_url: rpcUrl.trim() })
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.detail || 'Deployment failed. Check the node is running and the private key is correct.')
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="bg-emerald-900/20 border border-emerald-700 rounded-xl p-4 space-y-2">
        <p className="text-emerald-300 font-semibold">Token deployed successfully</p>
        <div className="font-mono text-xs space-y-1 text-gray-300">
          <p><span className="text-gray-500">Contract:</span> {result.contract_address}</p>
          <p><span className="text-gray-500">Symbol:</span> {result.token_symbol} · <span className="text-gray-500">Supply:</span> {result.total_supply.toLocaleString()} · <span className="text-gray-500">Minted:</span> {result.initial_minted.toLocaleString()}</p>
          <p><span className="text-gray-500">Tx:</span> {result.deploy_tx.slice(0, 20)}…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-amber-800/40 rounded-xl p-4 space-y-3">
      <p className="text-sm font-semibold text-amber-300">Deploy Token to Ethereum</p>
      <p className="text-xs text-gray-500">Uses the DD report parameters to deploy an RWAToken smart contract.</p>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Node RPC URL</label>
        <input
          value={rpcUrl}
          onChange={e => setRpcUrl(e.target.value)}
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
        />
      </div>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Private Key</label>
        <input
          type="password"
          value={privateKey}
          onChange={e => setPrivateKey(e.target.value)}
          placeholder="0xac0974be… (use Hardhat test key only)"
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
        />
        <p className="text-xs text-red-400/70 mt-1">Never use a real wallet key. Hardhat test keys only.</p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-3 py-2 text-red-300 text-xs">
          {error}
        </div>
      )}

      <button
        onClick={deploy}
        disabled={loading || !privateKey.trim()}
        className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold py-2 rounded-lg transition-colors text-sm"
      >
        {loading ? 'Deploying…' : 'Deploy Token'}
      </button>
    </div>
  )
}

export default function DDWorkflowDetail({ wfId, onBack }) {
  const [meta, setMeta] = useState(null)
  const { events, status, outputFile } = useWorkflow(wfId)
  const [showTokenize, setShowTokenize] = useState(false)

  useEffect(() => {
    if (!wfId) return
    getWorkflow(wfId).then(setMeta)
  }, [wfId])

  const currentStatus = status || meta?.status || 'pending'
  const currentOutput = outputFile || meta?.output_file
  const agentNames = [...new Set(events.map(e => e.agent_name))]

  const completedEvent = events.findLast?.(e => e.event_type === 'completed' && e.data?.dd_score != null)
    ?? events.slice().reverse().find(e => e.event_type === 'completed' && e.data?.dd_score != null)

  const ddScore = completedEvent?.data?.dd_score
  const recommendation = completedEvent?.data?.recommendation

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-start gap-4">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-300 mt-1 flex-shrink-0">← Back</button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs bg-amber-900/30 text-amber-400 border border-amber-700 px-2 py-0.5 rounded font-mono">DD</span>
            <span className={`text-xs font-mono px-2 py-0.5 rounded border ${STATUS_BADGE[currentStatus]}`}>
              {STATUS_ICON[currentStatus]} {currentStatus}
            </span>
            {agentNames.map(name => (
              <span key={name} className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded">{name}</span>
            ))}
          </div>
          <h2 className="text-lg font-semibold text-white">{meta?.query || '…'}</h2>
          {meta?.created_at && (
            <p className="text-xs text-gray-600 mt-1 font-mono">Started {new Date(meta.created_at).toLocaleString()}</p>
          )}
        </div>

        {currentStatus === 'completed' && ddScore != null && (
          <div className="text-right flex-shrink-0">
            <div className={`text-3xl font-bold tabular-nums ${SCORE_COLOR(ddScore)}`}>{ddScore}<span className="text-lg text-gray-500">/100</span></div>
            <div className={`text-xs font-mono mt-1 px-2 py-0.5 rounded border inline-block ${REC_BADGE(recommendation)}`}>{recommendation}</div>
          </div>
        )}
      </div>

      {currentStatus === 'running' && (
        <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-500 rounded-full"
            style={{ width: `${Math.min(90, (events.length / 30) * 100)}%`, transition: 'width 0.5s ease' }}
          />
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Agent Activity · {events.length} events
        </h3>
        <AgentTimeline events={events} status={currentStatus} />
      </div>

      {currentStatus === 'completed' && (
        <div>
          <button
            onClick={() => setShowTokenize(v => !v)}
            className="mb-3 bg-amber-600 hover:bg-amber-500 text-white font-semibold px-5 py-2 rounded-lg text-sm transition-colors"
          >
            {showTokenize ? 'Hide Tokenize' : 'Tokenize This Asset →'}
          </button>
          {showTokenize && <TokenizePanel wfId={wfId} />}
        </div>
      )}

      {currentStatus === 'completed' && currentOutput && (
        <OutputViewer outputFile={currentOutput} />
      )}

      {currentStatus === 'failed' && (
        <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
          Due diligence failed. Check the agent activity above for details.
        </div>
      )}
    </div>
  )
}
