import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export async function createSession() {
  const response = await axios.post(`${API_BASE}/api/session/create`)
  return response.data.session_id
}

export async function sendQuery(sessionId, query, maxResults = 5, onEvent) {
  // Use streaming endpoint
  const eventSource = new EventSource(
    `${API_BASE}/api/query/stream?session_id=${sessionId}&query=${encodeURIComponent(query)}&max_results=${maxResults}`
  )

  return new Promise((resolve, reject) => {
    let result = null

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (onEvent) {
          onEvent(data)
        }

        if (data.type === 'complete') {
          result = data.result
          eventSource.close()
          resolve(result)
        } else if (data.type === 'error') {
          eventSource.close()
          reject(new Error(data.error || 'Unknown error'))
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err)
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      eventSource.close()

      // Fallback to non-streaming endpoint
      axios.post(`${API_BASE}/api/query`, {
        session_id: sessionId,
        query: query,
        max_results: maxResults
      })
        .then(response => resolve(response.data.result))
        .catch(error => reject(error))
    }

    // Timeout after 2 minutes
    setTimeout(() => {
      if (!result) {
        eventSource.close()
        reject(new Error('Request timeout'))
      }
    }, 120000)
  })
}

export async function deleteSession(sessionId) {
  await axios.delete(`${API_BASE}/api/session/${sessionId}`)
}
