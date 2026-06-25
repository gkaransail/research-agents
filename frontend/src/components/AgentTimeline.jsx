import { useEffect, useRef } from 'react'

const AGENT_ICONS = {
  orchestrator:    '🎯',
  dd_orchestrator: '🏢',
  searcher:        '🔍',
  reader:          '📄',
  analyzer:        '🧠',
  writer:          '✍️',
  valuation:       '💰',
  regulatory:      '⚖️',
  risk:            '⚠️',
  dd_writer:       '📋',
}

const EVENT_COLORS = {
  planning:  'text-purple-400 border-purple-700',
  thinking:  'text-blue-400  border-blue-700',
  searching: 'text-yellow-400 border-yellow-700',
  reading:   'text-cyan-400  border-cyan-700',
  analyzing: 'text-orange-400 border-orange-700',
  writing:   'text-green-400  border-green-700',
  completed: 'text-emerald-400 border-emerald-700',
  error:     'text-red-400   border-red-700',
  info:      'text-gray-400  border-gray-700',
  started:   'text-indigo-400 border-indigo-700',
}

const EVENT_DOTS = {
  planning:  'bg-purple-500',
  thinking:  'bg-blue-500',
  searching: 'bg-yellow-500',
  reading:   'bg-cyan-500',
  analyzing: 'bg-orange-500',
  writing:   'bg-green-500',
  completed: 'bg-emerald-500',
  error:     'bg-red-500',
  info:      'bg-gray-500',
  started:   'bg-indigo-500',
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function AgentTimeline({ events, status }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-600">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <div className="text-sm">Waiting for agents to start...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-1 max-h-[420px] overflow-y-auto pr-1">
      {events.map((ev, i) => {
        const color = EVENT_COLORS[ev.event_type] || EVENT_COLORS.info
        const dot   = EVENT_DOTS[ev.event_type]  || EVENT_DOTS.info
        const icon  = AGENT_ICONS[ev.agent_name] || '🤖'
        const isLast = i === events.length - 1

        return (
          <div key={ev.id} className="flex gap-3 group">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${dot} ${isLast && status === 'running' ? 'animate-pulse' : ''}`} />
              {i < events.length - 1 && <div className="w-px flex-1 bg-gray-800 mt-1" />}
            </div>

            {/* Content */}
            <div className={`pb-2 border-l-0 flex-1 min-w-0 ${isLast ? '' : ''}`}>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm">{icon}</span>
                <span className="text-xs font-mono text-gray-500 uppercase tracking-wide">{ev.agent_name}</span>
                <span className={`text-xs font-mono px-1.5 py-0.5 rounded border ${color} opacity-80`}>{ev.event_type}</span>
                <span className="text-xs text-gray-600 ml-auto font-mono">{formatTime(ev.timestamp)}</span>
              </div>
              <p className="text-sm text-gray-300 leading-snug pl-5">{ev.message}</p>
              {ev.data && Object.keys(ev.data).length > 0 && ev.event_type !== 'planning' && (
                <div className="mt-1 pl-5">
                  {ev.data.queries && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ev.data.queries.map((q, qi) => (
                        <span key={qi} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">{q}</span>
                      ))}
                    </div>
                  )}
                  {ev.data.url && (
                    <a href={ev.data.url} target="_blank" rel="noreferrer"
                      className="text-xs text-indigo-400 hover:text-indigo-300 truncate block max-w-md">
                      {ev.data.url}
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
