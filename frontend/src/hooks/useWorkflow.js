import { useState, useEffect, useRef } from 'react'
import { createWorkflowSocket } from '../api'

export function useWorkflow(wfId) {
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState('pending')
  const [outputFile, setOutputFile] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!wfId) return

    setEvents([])
    setStatus('pending')
    setOutputFile(null)

    const ws = createWorkflowSocket(wfId)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'event') {
        setEvents(prev => {
          const exists = prev.some(ev => ev.id === msg.event.id)
          return exists ? prev : [...prev, msg.event]
        })
      } else if (msg.type === 'status') {
        setStatus(msg.status)
        if (msg.output_file) setOutputFile(msg.output_file)
      }
    }

    ws.onerror = () => setStatus(s => s === 'running' ? 'failed' : s)

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [wfId])

  return { events, status, outputFile }
}
