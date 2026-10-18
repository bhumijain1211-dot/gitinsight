import { useState } from 'react'
import RepoInput from './components/RepoInput.jsx'
import Chat from './components/Chat.jsx'

/*
  App
  ---
  This is the root component. It decides WHICH screen to show:
  - No repo ingested yet -> show RepoInput
  - Repo ingested (we have a repoId) -> show Chat

  This "lift state up" pattern is common in React: the parent (App) owns
  the shared state (repoId, repoInfo) and passes it down to children as
  props, since both RepoInput and Chat need to know about it.
*/
function App() {
  const [repoId, setRepoId] = useState(null)
  const [repoInfo, setRepoInfo] = useState(null)

  const handleIngested = (id, info) => {
    setRepoId(id)
    setRepoInfo(info)
  }

  const handleReset = () => {
    setRepoId(null)
    setRepoInfo(null)
  }

  return (
    <div className="app">
      {!repoId ? (
        <RepoInput onIngested={handleIngested} />
      ) : (
        <Chat repoId={repoId} repoInfo={repoInfo} onReset={handleReset} />
      )}
    </div>
  )
}

export default App
