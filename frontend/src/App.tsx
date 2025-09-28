import { useState } from 'react'
import axios from 'axios'
import { ReportDisplay } from './components/ReportDisplay/ReportDisplay'

interface EvidenceItem { source: string; title?: string; snippet?: string; score?: number; provenance_timestamp?: string; source_type?: string }
interface Verification { confidence: number; method: string; notes?: string }
interface AIDetection {
  is_ai_generated: boolean
  confidence: number
  method: string
  scores: Record<string, number>
  details: Record<string, any>
}
interface SAGNode {
  id: string
  type: string
  label: string
  uri?: string
}
interface SAGEdge {
  source: string
  target: string
  relation: string
  type: string
}
interface SAGData {
  analysis_id: string
  language: string
  content: string
  rdf_graph: Record<string, string>
  nodes: SAGNode[]
  edges: SAGEdge[]
  raw: string
  metadata: Record<string, any>
}

interface MultilingualData {
  detected_language: string
  processing_language: string
  translation_info?: {
    translated_text: string
    source_language: string
    target_language: string
    confidence: number
    method: string
  }
  cross_lingual_mappings: Array<{
    source_concept: string
    target_concept: string
    source_language: string
    target_language: string
    concept_key?: string
    confidence: number
    method: string
  }>
  supported_languages: string[]
}
interface ReportResponse {
  claim_id?: string | null
  verdict: string
  confidence: number
  evidence: EvidenceItem[]
  verification: Verification
  fallacies: Array<{ type: string; span?: string; explanation?: string }>
  ai_detection?: AIDetection
  sag?: SAGData
  multilingual?: MultilingualData
  provenance: Record<string, unknown>
}

type Mode = 'text' | 'url'

export function App() {
  const [mode, setMode] = useState<Mode>('text')
  const [text, setText] = useState('Vaccines cause autism')
  const [url, setUrl] = useState('https://example.org/article')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function analyze() {
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const payload = mode === 'url' ? { url } : { text }
      const res = await axios.post<ReportResponse>('http://localhost:8000/api/v1/analyze', payload)
      setReport(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail ? JSON.stringify(e.response.data.detail) : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '24px auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1>FailSafe</h1>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 8 }}>
        <label><input type="radio" name="mode" checked={mode==='text'} onChange={() => setMode('text')} /> Text</label>
        <label><input type="radio" name="mode" checked={mode==='url'} onChange={() => setMode('url')} /> URL</label>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {mode === 'text' ? (
          <input style={{ flex: 1, padding: 8 }} value={text} onChange={e => setText(e.target.value)} placeholder="Enter claim text" />
        ) : (
          <input style={{ flex: 1, padding: 8 }} value={url} onChange={e => setUrl(e.target.value)} placeholder="Enter article URL" />
        )}
        <button onClick={analyze} disabled={loading}>{loading ? 'Analyzing...' : 'Analyze'}</button>
      </div>
      {error && <pre style={{ color: 'crimson' }}>{error}</pre>}
      {report && (
        <ReportDisplay report={report} />
      )}
    </div>
  )
}
