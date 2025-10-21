/**
 * Enhanced WebSocket Service for Real-time Analysis Updates
 * Provides robust connection management and progress tracking
 */

class EnhancedWebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
    this.heartbeatInterval = null;
    this.listeners = new Map();
    this.isConnecting = false;
    this.connectionState = 'disconnected';
    
    // WebSocket URL from environment
    this.wsUrl = process.env.REACT_APP_WS_URL || 'wss://your-websocket-url';
  }

  /**
   * Connect to WebSocket server
   */
  connect(workflowId) {
    if (this.isConnecting || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }

    this.isConnecting = true;
    this.connectionState = 'connecting';

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.wsUrl}?workflow_id=${workflowId}`;
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
          console.log('WebSocket connected');
          this.connectionState = 'connected';
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.startHeartbeat();
          this.emit('connected');
          resolve();
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.connectionState = 'disconnected';
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          // Attempt reconnection if not a normal closure
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.connectionState = 'error';
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.stopHeartbeat();
    this.connectionState = 'disconnected';
  }

  /**
   * Send message to server
   */
  send(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected, cannot send message');
    return false;
  }

  /**
   * Subscribe to specific event types
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  /**
   * Unsubscribe from event
   */
  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to all listeners
   */
  emit(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(data) {
    const { type, payload } = data;

    switch (type) {
      case 'workflow_progress':
        this.emit('progress', payload);
        break;
      
      case 'agent_update':
        this.emit('agentUpdate', payload);
        break;
      
      case 'workflow_complete':
        this.emit('complete', payload);
        break;
      
      case 'workflow_error':
        this.emit('error', payload);
        break;
      
      case 'heartbeat':
        // Respond to heartbeat
        this.send({ type: 'heartbeat_ack' });
        break;
      
      default:
        console.log('Unknown message type:', type, payload);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.connectionState === 'disconnected') {
        this.connect();
      }
    }, delay);
  }

  /**
   * Get current connection state
   */
  getConnectionState() {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}

// React Hook for WebSocket integration
export const useEnhancedWebSocket = (workflowId) => {
  const [wsService] = useState(() => new EnhancedWebSocketService());
  const [connectionState, setConnectionState] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [progress, setProgress] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!workflowId) return;

    // Set up event listeners
    const handleConnected = () => {
      setConnectionState('connected');
      setError(null);
    };

    const handleDisconnected = () => {
      setConnectionState('disconnected');
    };

    const handleError = (err) => {
      setError(err);
      setConnectionState('error');
    };

    const handleProgress = (data) => {
      setProgress(data);
      setLastMessage({ type: 'progress', data });
    };

    const handleAgentUpdate = (data) => {
      setLastMessage({ type: 'agentUpdate', data });
    };

    const handleComplete = (data) => {
      setLastMessage({ type: 'complete', data });
      setConnectionState('completed');
    };

    // Register listeners
    wsService.on('connected', handleConnected);
    wsService.on('disconnected', handleDisconnected);
    wsService.on('error', handleError);
    wsService.on('progress', handleProgress);
    wsService.on('agentUpdate', handleAgentUpdate);
    wsService.on('complete', handleComplete);

    // Connect
    wsService.connect(workflowId).catch(err => {
      console.error('Failed to connect WebSocket:', err);
      setError(err);
    });

    // Cleanup
    return () => {
      wsService.off('connected', handleConnected);
      wsService.off('disconnected', handleDisconnected);
      wsService.off('error', handleError);
      wsService.off('progress', handleProgress);
      wsService.off('agentUpdate', handleAgentUpdate);
      wsService.off('complete', handleComplete);
      wsService.disconnect();
    };
  }, [workflowId, wsService]);

  return {
    connectionState,
    lastMessage,
    progress,
    error,
    isConnected: wsService.isConnected(),
    send: wsService.send.bind(wsService)
  };
};

// Singleton instance for global use
const globalWebSocketService = new EnhancedWebSocketService();

export default globalWebSocketService;
export { EnhancedWebSocketService };
