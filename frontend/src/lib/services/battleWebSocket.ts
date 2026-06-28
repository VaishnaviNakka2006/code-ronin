// src/lib/services/battleWebSocket.ts
import { supabase } from '$lib/supabaseClient';
import { writable, type Writable } from 'svelte/store';

// ---------- Types ----------
type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'in_queue' | 'matched';

interface BattleEvent {
  type: string;
  [key: string]: any;
}

type MessageHandler = (event: BattleEvent) => void;

// ---------- Service Class ----------
class BattleWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms, doubles each attempt
  private reconnectTimer: number | null = null;
  private messageHandlers: MessageHandler[] = [];
  private pendingMessages: any[] = [];
  private isConnected = false;

  // Public stores
  public status: Writable<WebSocketStatus> = writable('disconnected');
  public roomId: Writable<string | null> = writable(null);
  public opponentUsername: Writable<string | null> = writable(null);
  public difficulty: Writable<string | null> = writable(null);

  // ---------- Public Methods ----------
  async connect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      // Wait for connection to complete
      return new Promise((resolve) => {
        const check = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(check);
            resolve();
          }
          if (this.ws?.readyState === WebSocket.CLOSED) {
            clearInterval(check);
            this.connect(); // retry
          }
        }, 100);
      });
    }

    this.status.set('connecting');

    // Get current session token
    const session = await supabase.auth.getSession();
    const token = session.data.session?.access_token;
    if (!token) {
      console.error('Battle WebSocket: No auth token available');
      this.status.set('disconnected');
      throw new Error('No auth token');
    }

    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBase}/battle/ws?token=${token}`;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(wsUrl);
        this.ws.onopen = () => {
          this.isConnected = true;
          this.status.set('connected');
          this.reconnectAttempts = 0;
          this.clearReconnectTimer();
          this.flushPendingMessages();
          console.log('Battle WebSocket connected');
          resolve();
        };
        this.ws.onmessage = this.handleWebSocketMessage.bind(this);
        this.ws.onclose = this.onClose.bind(this);
        this.ws.onerror = (event) => {
          console.error('Battle WebSocket error:', event);
          // Will be followed by onclose
        };
      } catch (err) {
        this.status.set('disconnected');
        reject(err);
      }
    });
  }

  disconnect(): void {
    this.clearReconnectTimer();
    this.isConnected = false;
    this.pendingMessages = [];
    if (this.ws) {
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

  // Matchmaking commands (Phase 8.1)
  joinQueue(difficulty: string): void {
    this.send({ type: 'join_queue', difficulty });
  }

  leaveQueue(): void {
    this.send({ type: 'leave_queue' });
  }

  // Battle room commands (Phase 8.2.1)
  joinRoom(roomId: string): void {
    this.send({ type: 'join_room', room_id: roomId });
  }

  ready(): void {
    this.send({ type: 'ready' });
  }

  notReady(): void {
    this.send({ type: 'not_ready' });
  }

  // Register a message handler – returns an unsubscribe function
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index !== -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  // ---------- Private Methods ----------
  private send(message: any): void {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for later
      this.pendingMessages.push(message);
      // If not connected, trigger reconnect
      if (!this.isConnected) {
        this.connect().catch(console.error);
      }
    }
  }

  private flushPendingMessages(): void {
    while (this.pendingMessages.length > 0) {
      const msg = this.pendingMessages.shift();
      if (msg && this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(msg));
      }
    }
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
    this.isConnected = false;
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

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    this.reconnectTimer = window.setTimeout(() => {
      this.connect().catch(console.error);
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
    // Update stores based on event type (Phase 8.1)
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
        // For room_state and other events, just pass through
        break;
    }

    // Notify all registered handlers
    for (const handler of this.messageHandlers) {
      try {
        handler(data);
      } catch (e) {
        console.error('Error in message handler:', e);
      }
    }
  }
}

// ---------- Singleton Export ----------
export const battleWS = new BattleWebSocketService();