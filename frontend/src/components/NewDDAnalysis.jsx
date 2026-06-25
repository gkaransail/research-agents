import { useState } from 'react'
import { startDDAnalysis } from '../api'

const ASSET_TYPES = ['real estate', 'commercial property', 'infrastructure', 'private equity fund', 'commodity']

const DEPTHS = [
  { value: 1, label: 'Quick', desc: '3 sources · ~1 min' },
  { value: 2, label: 'Standard', desc: '5 sources · ~2 min' },
  { value: 3, label: 'Deep', desc: '8 sources · ~4 min' },
]

export default function NewDDAnalysis({ onCreated, onClose }) {
  const [assetName, setAssetName] = useState('')
  const [assetType, setAssetType] = useState('real estate')
  const [assetLocation, setAssetLocation] = useState('')
  const [assetDescription, setAssetDescription] = useState('')
  const [depth, setDepth] = useState(2)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    if (!assetName.trim() || !assetLocation.trim()) return
    setLoading(true)
    setError('')
    try {
      const wf = await startDDAnalysis({
        asset_name: assetName.trim(),
        asset_type: assetType,
        asset_location: assetLocation.trim(),
        asset_description: assetDescription.trim(),
        depth,
      })
      onCreated(wf)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start analysis. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-white">New Due Diligence</h2>
            <p className="text-xs text-gray-500 mt-0.5">AI agents will research valuation, regulatory status, and risks</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-2xl leading-none">&times;</button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Asset Name</label>
            <input
              value={assetName}
              onChange={e => setAssetName(e.target.value)}
              placeholder="e.g. Marina Bay Residences Unit 2401"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Asset Type</label>
              <select
                value={assetType}
                onChange={e => setAssetType(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
              >
                {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Location</label>
              <input
                value={assetLocation}
                onChange={e => setAssetLocation(e.target.value)}
                placeholder="e.g. Singapore"
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Description <span className="text-gray-600">(optional)</span></label>
            <textarea
              value={assetDescription}
              onChange={e => setAssetDescription(e.target.value)}
              placeholder="Brief description of the asset..."
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Research Depth</label>
            <div className="grid grid-cols-3 gap-2">
              {DEPTHS.map(d => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDepth(d.value)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    depth === d.value
                      ? 'border-amber-500 bg-amber-500/10 text-amber-300'
                      : 'border-gray-700 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  <div className="font-semibold text-sm">{d.label}</div>
                  <div className="text-xs mt-0.5 opacity-70">{d.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-amber-900/20 border border-amber-800/50 rounded-lg px-3 py-2 text-xs text-amber-400/80">
            Agents run: Valuation → Regulatory → Risk → DD Report writer
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !assetName.trim() || !assetLocation.trim()}
            className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
          >
            {loading ? 'Starting analysis...' : 'Run Due Diligence'}
          </button>
        </form>
      </div>
    </div>
  )
}
