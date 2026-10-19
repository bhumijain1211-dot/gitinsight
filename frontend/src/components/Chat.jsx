import { useState, useRef, useEffect } from 'react'

const API_BASE = 'http://localhost:5000'

function Chat({ repoId, repoInfo, onReset }) {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleAsk = async () => {
    if (!question.trim() || loading) return

    const userMessage = { role: 'user', text: question }
    setMessages((prev) => [...prev, userMessage])
    setQuestion('')
    setLoading(true)

    const chatHistory = []
    for (let i = 0; i < messages.length - 1; i += 2) {
      if (messages[i]?.role === 'user' && messages[i + 1]?.role === 'assistant') {
        chatHistory.push({ question: messages[i].text, answer: messages[i + 1].text })
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repoId, question: userMessage.text, chat_history: chatHistory }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Something went wrong')
      setMessages((prev) => [...prev, { role: 'assistant', text: data.answer, sources: data.sources }])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', text: `Error: ${err.message}`, sources: [] }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  return (
    <div className="chat">
      <div className="chat-header">
        <div className="repo-badge">
          <span className="dot" />
          <span className="name">{repoId}</span>
          {repoInfo && (
            <span className="stats">
              {repoInfo.num_files} files · {repoInfo.num_chunks} chunks
            </span>
          )}
        </div>
        <button className="btn-ghost" onClick={onReset}>+ new repo</button>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="thinking" style={{ marginLeft: 0 }}>
            # ask anything about this codebase
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === 'user' ? (
            <div className="msg-block" key={i}>
              <div className="msg-line user">
                <span className="prompt-symbol">❯</span>
                <span className="text">{msg.text}</span>
              </div>
            </div>
          ) : (
            <div className="msg-block" key={i}>
              <div className="msg-line assistant">
                <span className="prompt-symbol">›</span>
                <span className="text" style={{ flex: 1 }}>
                  <div className="assistant-panel">
                    {msg.text}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        <span className="label">sources</span>
                        {msg.sources.map((s, j) => (
                          <span className="source-chip" key={j}>{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </span>
              </div>
            </div>
          )
        )}

        {loading && <div className="thinking">thinking</div>}
        <div ref={bottomRef} />
      </div>

      <div className="input-row">
        <textarea
          placeholder="Ask something about this repo…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          rows={1}
        />
        <button className="btn-amber" onClick={handleAsk} disabled={loading}>send</button>
      </div>
    </div>
  )
}

export default Chat
