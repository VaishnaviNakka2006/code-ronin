// src/lib/services/battleWebSocket.ts
import { supabase } from '$lib/supabaseClient';
import { writable, type Writable } from 'svelte/store';

// ---------- Types ----------
type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'in_queue' | 'matched';

interface BattleEvent {
  type: string;
  [key: string]: any;
}

// ---------- Service Class ----------
class BattleWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms, doubles each attempt
  private reconnectTimer: number | null = null;
  private messageHandler: ((event: BattleEvent) => void) | null = null;

  // Public stores
  public status: Writable<WebSocketStatus> = writable('disconnected');
  public roomId: Writable<string | null> = writable(null);
  public opponentUsername: Writable<string | null> = writable(null);
  public difficulty: Writable<string | null> = writable(null);

  // ---------- Public Methods ----------
  async connect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) return; // already connecting

    this.status.set('connecting');

    // Get current session token
    const session = await supabase.auth.getSession();
    const token = session.data.session?.access_token;
    if (!token) {
      console.error('Battle WebSocket: No auth token available');
      this.status.set('disconnected');
      return;
    }

    // Build WebSocket URL with token
    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBase}/battle/ws?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.onopen = this.onOpen.bind(this);
      this.ws.onmessage = this.handleWebSocketMessage.bind(this);
      this.ws.onclose = this.onClose.bind(this);
      this.ws.onerror = this.onError.bind(this);
    } catch (err) {
      console.error('Battle WebSocket connection error:', err);
      this.status.set('disconnected');
    }
  }

  disconnect(): void {
    this.clearReconnectTimer();
    if (this.ws) {
      // Remove event listeners to prevent reconnection attempts
      this.ws.onopen = null;
      this.ws.onclose = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }
    this.status.set('disconnected');
    this.resetStores();
  }

  joinQueue(difficulty: string): void {
    this.send({ type: 'join_queue', difficulty });
  }

  leaveQueue(): void {
    this.send({ type: 'leave_queue' });
  }

  // Register a global message handler (optional)
  onMessage(handler: (event: BattleEvent) => void): void {
    this.messageHandler = handler;
  }

  // ---------- Private Methods ----------
  private send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('Battle WebSocket: Cannot send, connection not open');
    }
  }

  private onOpen(): void {
    console.log('Battle WebSocket connected');
    this.status.set('connected');
    this.reconnectAttempts = 0;
    this.clearReconnectTimer();
  }

  private handleWebSocketMessage(event: MessageEvent): void {
    try {
      const data: BattleEvent = JSON.parse(event.data);
      this.handleMessage(data);
    } catch (e) {
      console.error('Battle WebSocket: Invalid JSON received', e);
    }
  }

  private onClose(event: CloseEvent): void {
    console.log(`Battle WebSocket closed: ${event.code} ${event.reason}`);
    this.ws = null;
    this.status.set('disconnected');

    // Attempt reconnect if not closed by user (code 1000) and not max attempts
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else {
      this.status.set('disconnected');
      this.resetStores();
    }
  }

  private onError(event: Event): void {
    console.error('Battle WebSocket error:', event);
    // onClose will be called after this
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    this.reconnectTimer = window.setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private resetStores(): void {
    this.roomId.set(null);
    this.opponentUsername.set(null);
    this.difficulty.set(null);
  }

  private handleMessage(data: BattleEvent): void {
    // Update stores based on event type
    switch (data.type) {
      case 'connected':
        this.status.set('connected');
        break;
      case 'queue_joined':
        this.status.set('in_queue');
        this.difficulty.set(data.difficulty);
        break;
      case 'queue_left':
        this.status.set('connected');
        this.difficulty.set(null);
        break;
      case 'battle_found':
        this.status.set('matched');
        this.roomId.set(data.room_id);
        this.opponentUsername.set(data.opponent_username);
        this.difficulty.set(data.difficulty);
        break;
      case 'error':
        console.error('Battle WebSocket error from server:', data.message);
        break;
      default:
        // Pass through unknown events
        break;
    }

    // Forward to custom handler if set
    if (this.messageHandler) {
      this.messageHandler(data);
    }
  }
}

// ---------- Singleton Export ----------
export const battleWS = new BattleWebSocketService();