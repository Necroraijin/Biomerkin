import io from 'socket.io-client';
import React from 'react';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(workflowId) {
    if (this.socket && this.socket.connected) {
      this.disconnect();
    }

    const serverUrl = process.env.REACT_APP_WS_URL || process.env.REACT_APP_API_URL || 'http://localhost:3001';
    
    this.socket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      maxHttpBufferSize: 1e6,
    });

    this.setupEventListeners();
    
    if (workflowId) {
      this.joinWorkflow(workflowId);
    }

    return this.socket;
  }

  setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected:', this.socket.id);
      this.reconnectAttempts = 0;
      this.emit('connection', { status: 'connected', id: this.socket.id });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('connection', { status: 'disconnected', reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      this.emit('connection', { 
        status: 'error', 
        error: error.message,
        attempts: this.reconnectAttempts 
      });
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts');
      this.emit('connection', { status: 'reconnected', attempts: attemptNumber });
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error);
      this.emit('connection', { status: 'reconnect_error', error: error.message });
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
      this.emit('connection', { status: 'reconnect_failed' });
    });

    // Analysis-specific events
    this.socket.on('workflow-progress', (data) => {
      console.log('Workflow progress:', data);
      this.emit('workflow-progress', data);
    });

    this.socket.on('workflow-complete', (data) => {
      console.log('Workflow complete:', data);
      this.emit('workflow-complete', data);
    });

    this.socket.on('workflow-error', (data) => {
      console.error('Workflow error:', data);
      this.emit('workflow-error', data);
    });

    this.socket.on('agent-status', (data) => {
      console.log('Agent status update:', data);
      this.emit('agent-status', data);
    });

    this.socket.on('system-notification', (data) => {
      console.log('System notification:', data);
      this.emit('system-notification', data);
    });
  }

  joinWorkflow(workflowId) {
    if (this.socket && this.socket.connected) {
      console.log('Joining workflow:', workflowId);
      this.socket.emit('join-workflow', workflowId);
    }
  }

  leaveWorkflow(workflowId) {
    if (this.socket && this.socket.connected) {
      console.log('Leaving workflow:', workflowId);
      this.socket.emit('leave-workflow', workflowId);
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket event callback:', error);
        }
      });
    }
  }

  // Send message to server
  send(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot send:', event, data);
    }
  }

  disconnect() {
    if (this.socket) {
      console.log('Disconnecting WebSocket');
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  isConnected() {
    return this.socket && this.socket.connected;
  }

  getConnectionState() {
    if (!this.socket) return 'disconnected';
    if (this.socket.connected) return 'connected';
    if (this.socket.connecting) return 'connecting';
    return 'disconnected';
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export const useWebSocket = (workflowId) => {
  const [connectionState, setConnectionState] = React.useState('disconnected');
  const [lastMessage, setLastMessage] = React.useState(null);

  React.useEffect(() => {
    const handleConnection = (data) => {
      setConnectionState(data.status);
    };

    const handleMessage = (data) => {
      setLastMessage({ timestamp: Date.now(), data });
    };

    webSocketService.on('connection', handleConnection);
    webSocketService.on('workflow-progress', handleMessage);
    webSocketService.on('workflow-complete', handleMessage);
    webSocketService.on('workflow-error', handleMessage);

    if (workflowId) {
      webSocketService.connect(workflowId);
    }

    return () => {
      webSocketService.off('connection', handleConnection);
      webSocketService.off('workflow-progress', handleMessage);
      webSocketService.off('workflow-complete', handleMessage);
      webSocketService.off('workflow-error', handleMessage);
      
      if (workflowId) {
        webSocketService.leaveWorkflow(workflowId);
      }
    };
  }, [workflowId]);

  return {
    connectionState,
    lastMessage,
    send: webSocketService.send.bind(webSocketService),
    isConnected: webSocketService.isConnected.bind(webSocketService),
  };
};

export default webSocketService;