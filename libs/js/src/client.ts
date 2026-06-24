/**
 * @handshake-prompt/client
 * Framework-agnostic browser SDK for the Handshake Prompt Protocol.
 */

export interface SchemaField {
  key: string
  label?: string
  type: 'string' | 'int' | 'float' | 'bool' | 'datetime' | 'enum' | string
  required?: boolean
  example?: any
  desc?: string
  options?: { value: any; label?: string }[]
  [extra: string]: any
}

export interface SessionInfo {
  sessionId: string
  token: string
  wsUrl: string
  contextUrl: string
  actionUrl: string
  diffUrl: string
  notifyUrl: string
  expiresIn: number
}

export interface FieldEntry {
  value: any
  by: 'empty' | 'user' | 'ai' | 'user_edit'
  at: string
}

export type Context = Record<string, FieldEntry>

export type EventType = 'connected' | 'action' | 'done' | 'error'

export interface ActionEvent  { type: 'action';   key: string; value: any }
export interface DoneEvent    { type: 'done';     applied: number; rejected: string[]; missing: string[] }
export interface ErrorEvent   { type: 'error';    msg: string }
export interface ConnectedEvent { type: 'connected'; sessionId: string; mode: string }

export type HandshakeEvent = ActionEvent | DoneEvent | ErrorEvent | ConnectedEvent

export interface ClientOptions {
  /** Base URL of the service. Default: location.origin */
  baseUrl?: string
  /** Endpoint prefix. Default: '/handshake' */
  prefix?: string
  /** WebSocket prefix. Default: '/ws/handshake' */
  wsPrefix?: string
  /** Custom fetch (e.g. with credentials). Default: window.fetch */
  fetch?: typeof fetch
}

export interface CreateSessionRequest {
  mode?: string
  schema?: SchemaField[]
  context?: Record<string, any>
  meta?: Record<string, any>
}

export class HandshakeClient {
  private baseUrl:  string
  private prefix:   string
  private wsPrefix: string
  private _fetch:   typeof fetch

  session: SessionInfo | null = null
  private ws: WebSocket | null = null
  private listeners = new Map<EventType, Set<(e: any) => void>>()

  constructor(opts: ClientOptions = {}) {
    this.baseUrl  = (opts.baseUrl  ?? (typeof location !== 'undefined' ? location.origin : '')).replace(/\/$/, '')
    this.prefix   = (opts.prefix   ?? '/handshake').replace(/\/$/, '')
    this.wsPrefix = (opts.wsPrefix ?? '/ws/handshake').replace(/\/$/, '')
    this._fetch   = opts.fetch ?? ((...a) => fetch(...a))
  }

  // ── Lifecycle ──────────────────────────────────────────

  /**
   * Create a new handshake session. Browser side calls this when user
   * clicks the "AI Action" button.
   */
  async createSession(req: CreateSessionRequest = {}): Promise<SessionInfo> {
    const res = await this._fetch(`${this.baseUrl}${this.prefix}/session`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
    if (!res.ok) throw new Error(`createSession failed: ${res.status}`)
    const data = await res.json() as SessionInfo
    this.session = data
    return data
  }

  /**
   * Open the WebSocket channel to receive real-time push events from the server.
   * Must be called after createSession().
   */
  connect(): WebSocket {
    if (!this.session) throw new Error('no session; call createSession() first')
    const proto = (typeof location !== 'undefined' && location.protocol === 'https:') ? 'wss' : 'ws'
    const host  = this.baseUrl.replace(/^https?:\/\//, '') || (typeof location !== 'undefined' ? location.host : '')
    const url   = `${proto}://${host}${this.session.wsUrl}?token=${encodeURIComponent(this.session.token)}`

    this.ws = new WebSocket(url)
    this.ws.addEventListener('message', (e) => {
      try {
        const msg = JSON.parse(e.data) as HandshakeEvent
        this._emit(msg.type, msg)
      } catch {}
    })
    this.ws.addEventListener('error', () => {
      this._emit('error', { type: 'error', msg: 'websocket error' })
    })
    return this.ws
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  // ── Event subscription ─────────────────────────────────

  on(type: 'connected', cb: (e: ConnectedEvent) => void): () => void
  on(type: 'action',    cb: (e: ActionEvent)    => void): () => void
  on(type: 'done',      cb: (e: DoneEvent)      => void): () => void
  on(type: 'error',     cb: (e: ErrorEvent)     => void): () => void
  on(type: EventType, cb: (e: any) => void): () => void {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(cb)
    return () => this.listeners.get(type)?.delete(cb)
  }

  private _emit(type: EventType, payload: any) {
    this.listeners.get(type)?.forEach((cb) => {
      try { cb(payload) } catch {}
    })
  }

  // ── User edit notification ─────────────────────────────

  /**
   * Notify the server that the user manually edited a field.
   * Prefer the WebSocket channel (faster, no round-trip),
   * with HTTP as fallback.
   */
  notifyUserEdit(key: string, value: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'userEdit', key, value }))
      return
    }
    if (!this.session) return
    this._fetch(`${this.baseUrl}${this.session.notifyUrl}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value }),
    }).catch(() => {})
  }

  // ── Prompt generation ──────────────────────────────────

  /**
   * Build the handshake prompt text that the user copy-pastes to their Agent.
   *
   * @param customInstructions Optional service-specific instructions
   * @param skillName  Hint Agent which skill to load (e.g. "form-fill")
   */
  buildPrompt(opts: {
    title?: string
    customInstructions?: string
    skillName?: string
  } = {}): string {
    if (!this.session) throw new Error('no session; call createSession() first')
    const { title = 'Handshake Prompt', customInstructions, skillName } = opts
    const s = this.session

    return [
      `# ${title}`,
      ``,
      `## Credentials`,
      `- sessionId: ${s.sessionId}`,
      `- token: ${s.token}`,
      `- baseUrl: ${this.baseUrl}`,
      `- expiresIn: ${s.expiresIn}s`,
      ...(skillName ? [`- skill: ${skillName}`] : []),
      ``,
      ...(customInstructions ? [`## Instructions`, customInstructions, ``] : []),
      `## Usage`,
      `1. GET  ${this.baseUrl}${s.contextUrl}  (header X-Handshake-Token: <token>)`,
      `2. POST ${this.baseUrl}${s.actionUrl}   {"actions":[{"type":"set","key":...,"value":...}]}`,
      ``,
      `## Security`,
      `- This token is single-use and expires shortly.`,
      `- Do NOT forward this prompt to others.`,
      `- The server will reject any AI attempt to overwrite user-filled fields.`,
      ``,
      `## Waiting for user's request...`,
    ].join('\n')
  }

  /**
   * Copy the handshake prompt to clipboard.
   * Returns true on success.
   */
  async copyPrompt(opts?: Parameters<HandshakeClient['buildPrompt']>[0]): Promise<boolean> {
    const text = this.buildPrompt(opts)
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      return false
    }
  }
}
