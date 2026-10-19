import { useState } from 'react'

const API_BASE = 'http://localhost:5000'

function RepoInput({ onIngested }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleIngest = async () => {
    if (!repoUrl.trim()) return
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/api/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to ingest repo')
      onIngested(data.repo_id, data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleIngest()
  }

  return (
    <div className="repo-input">
      <div className="brand">
        <span className="brand-dot" />
        <h1>gitinsight</h1>
      </div>
      <p>Ask questions about any public GitHub repo in plain English. Paste a URL below to index it.</p>

      <div className="terminal-frame">
        <div className="terminal-titlebar">
          <span /><span /><span />
          <span className="label">ingest — zsh</span>
        </div>
        <div className="terminal-body">
          <div className="prompt-line">
            <span className="prompt-symbol">❯</span>
            <span className="prompt-cmd">gitinsight ingest</span>
            <input
              type="text"
              placeholder="https://github.com/owner/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              autoFocus
            />
          </div>
          <div className="run-row">
            <button className="btn-amber" onClick={handleIngest} disabled={loading}>
              {loading ? 'indexing repo…' : 'run'}
            </button>
          </div>
          {error && <div className="error-line">{error}</div>}
        </div>
      </div>

      <div className="hint-repos"># try: https://github.com/pallets/flask</div>
    </div>
  )
}

export default RepoInput
