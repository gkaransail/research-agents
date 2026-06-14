import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { getOutput } from '../api'

export default function OutputViewer({ outputFile }) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  const filename = outputFile ? outputFile.split('/').pop() : null

  useEffect(() => {
    if (!filename) return
    setLoading(true)
    getOutput(filename)
      .then(setContent)
      .catch(() => setContent('Failed to load report.'))
      .finally(() => setLoading(false))
  }, [filename])

  function copyToClipboard() {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!outputFile) return null

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Research Report</h3>
        <div className="flex gap-2">
          {content && (
            <button
              onClick={copyToClipboard}
              className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white px-3 py-1 rounded transition-colors"
            >
              {copied ? 'Copied!' : 'Copy MD'}
            </button>
          )}
          <span className="text-xs font-mono text-gray-600 bg-gray-800 px-2 py-1 rounded">{filename}</span>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 overflow-y-auto max-h-[600px]">
        {loading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            Loading report...
          </div>
        ) : (
          <div className="prose-custom">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
