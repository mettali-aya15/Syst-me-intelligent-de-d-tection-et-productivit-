let socket = null
let reconnectDelay = 1000      // 1s
let maxDelay = 10000           // 10s
let reconnectTimer = null
let listeners = []

const WS_URL = `${import.meta.env.VITE_WS_BASE_URL}/ws/events`

function connect() {
  if (socket && socket.readyState === WebSocket.OPEN) return

  socket = new WebSocket(WS_URL)

  socket.onopen = () => {
    console.log("✅ WebSocket connecté")
    reconnectDelay = 1000
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    listeners.forEach(cb => cb(data))
  }

  socket.onclose = () => {
    console.warn("⚠️ WebSocket déconnecté – reconnexion...")
    scheduleReconnect()
  }

  socket.onerror = () => {
    socket.close()
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    reconnectDelay = Math.min(reconnectDelay * 2, maxDelay)
    connect()
  }, reconnectDelay)
}

export function subscribe(callback) {
  listeners.push(callback)
  connect()
}

export function unsubscribe(callback) {
  listeners = listeners.filter(cb => cb !== callback)
}

export function disconnect() {
  if (socket) socket.close()
  socket = null
}
