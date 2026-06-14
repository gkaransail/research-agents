import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const startResearch = (query, depth = 2) =>
  api.post('/workflows', { query, depth }).then(r => r.data)

export const listWorkflows = () =>
  api.get('/workflows').then(r => r.data)

export const getWorkflow = (id) =>
  api.get(`/workflows/${id}`).then(r => r.data)

export const deleteWorkflow = (id) =>
  api.delete(`/workflows/${id}`)

export const listOutputs = () =>
  api.get('/outputs').then(r => r.data)

export const getOutput = (filename) =>
  api.get(`/outputs/${filename}`).then(r => r.data)

export const getAgents = () =>
  api.get('/agents').then(r => r.data)

export function createWorkflowSocket(wfId) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return new WebSocket(`${proto}://${window.location.host}/ws/${wfId}`)
}
