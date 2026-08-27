import type { DashboardData } from '@/types'

export type SocketEvent =
  | { type: 'environment:update'; payload: DashboardData['environment'] }
  | { type: 'inventory:update'; payload: { stock: number; alerts: number } }
  | { type: 'recognition:new'; payload: DashboardData['recognitions'][number] }
  | { type: 'system:update'; payload: { cpu: string; memory: string; latency: string } }

type EventHandler = (event: SocketEvent) => void

export class RealtimeSocket {
  private socket?: WebSocket
  private timer?: number
  private handlers = new Set<EventHandler>()
  private connected = false

  connect() {
    const useMock = import.meta.env.VITE_USE_MOCK !== 'false'
    if (useMock) {
      this.connected = true
      this.timer = window.setInterval(() => this.emitMock(), 4200)
      return
    }

    const url = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/notify'
    this.socket = new WebSocket(url)
    this.socket.onopen = () => { this.connected = true }
    this.socket.onclose = () => { this.connected = false }
    this.socket.onerror = () => { this.connected = false }
    this.socket.onmessage = (message) => {
      try {
        this.emit(JSON.parse(message.data) as SocketEvent)
      } catch {
        // Ignore malformed upstream messages and keep the realtime channel alive.
      }
    }
  }

  disconnect() {
    if (this.timer) window.clearInterval(this.timer)
    this.socket?.close()
    this.handlers.clear()
    this.connected = false
  }

  on(handler: EventHandler) {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  isConnected() {
    return this.connected
  }

  private emit(event: SocketEvent) {
    this.handlers.forEach((handler) => handler(event))
  }

  private emitMock() {
    const temperature = +(3.2 + Math.random() * 0.9).toFixed(1)
    const humidity = +(86 + Math.random() * 5).toFixed(1)
    const base = new Date()
    const time = base.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
    this.emit({
      type: 'environment:update',
      payload: {
        temperature,
        humidity,
        temperatureState: temperature > 6 ? 'warning' : 'online',
        humidityState: humidity > 94 ? 'warning' : 'online',
        trend: Array.from({ length: 16 }, (_, index) => ({
          time,
          temperature: +(temperature - 0.4 + Math.random() * 0.8).toFixed(1),
          humidity: +(humidity - 2 + Math.random() * 4).toFixed(1),
        })),
      },
    })
    this.emit({
      type: 'system:update',
      payload: {
        cpu: `${Math.round(32 + Math.random() * 14)}%`,
        memory: `${Math.round(48 + Math.random() * 8)}%`,
        latency: `${Math.round(16 + Math.random() * 8)} ms`,
      },
    })
  }
}

export const realtimeSocket = new RealtimeSocket()
