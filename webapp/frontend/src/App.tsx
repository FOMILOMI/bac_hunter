import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

type Parameter = {
  name: string
  kind: 'argument' | 'option'
  type: string
  required: boolean
  default?: any
  help?: string
  flags?: string[]
}

type DiscoveredCommand = {
  name: string
  function_name: string
  module: string
  help?: string
  parameters: Parameter[]
}

type RunStatus = {
  id: string
  command: string
  args: string[]
  status: 'pending'|'running'|'completed'|'failed'|'canceled'
  return_code?: number
  last_log_offset?: number
}

const API_BASE = ''

function App() {
  const [commands, setCommands] = useState<DiscoveredCommand[]>([])
  const [selected, setSelected] = useState<DiscoveredCommand | null>(null)
  const [values, setValues] = useState<Record<string, any>>({})
  const [run, setRun] = useState<RunStatus | null>(null)
  const [logs, setLogs] = useState<string>('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/commands`).then(r => r.json()).then(setCommands)
  }, [])

  const form = useMemo(() => {
    if (!selected) return null
    const onChange = (name: string, v: any) => setValues(prev => ({...prev, [name]: v}))
    return (
      <div className="form">
        {selected.parameters.map(p => (
          <div className="field" key={p.name}>
            <label>{p.name} {p.required ? '*' : ''}</label>
            {p.help && <small>{p.help}</small>}
            {p.kind === 'argument' || p.type.startsWith('array') ? (
              <input placeholder={p.type}
                     onChange={e => onChange(p.name, p.type.startsWith('array') ? e.target.value.split(',') : e.target.value)} />
            ) : (
              <input placeholder={p.type}
                     onChange={e => onChange(p.name, e.target.value)} />
            )}
          </div>
        ))}
        <button onClick={async () => {
          if (!selected) return
          const res = await fetch(`${API_BASE}/api/commands/${selected.name}/execute`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({parameters: values, stream: true})
          })
          const data = await res.json()
          setLogs('')
          const rres = await fetch(`${API_BASE}/api/runs/${data.run_id}`)
          setRun(await rres.json())
          const wsProto = location.protocol === 'https:' ? 'wss' : 'ws'
          const ws = new WebSocket(`${wsProto}://${location.host}/ws/runs/${data.run_id}`)
          ws.onmessage = (ev) => setLogs(prev => prev + ev.data)
          ws.onerror = () => ws.close()
          ws.onclose = () => (wsRef.current = null)
          wsRef.current = ws
        }}>Run</button>
      </div>
    )
  }, [selected, values])

  return (
    <div className="container">
      <aside>
        <h2>BAC Hunter</h2>
        <ul>
          {commands.map(c => (
            <li key={c.name} className={selected?.name===c.name? 'active': ''}
                onClick={() => {setSelected(c); setValues({}); setRun(null); setLogs('')}}>
              {c.name}
            </li>
          ))}
        </ul>
      </aside>
      <main>
        {selected ? (
          <>
            <h3>{selected.name}</h3>
            <p>{selected.help}</p>
            {form}
            {run && (
              <div className={`run ${run.status}`}>
                <div>Run: {run.id} — status: {run.status} rc: {run.return_code ?? '-'}</div>
              </div>
            )}
            <pre className="logs">{logs}</pre>
          </>
        ) : (
          <div>Select a command to begin.</div>
        )}
      </main>
    </div>
  )
}

export default App
