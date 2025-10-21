import { useEffect, useState, useRef } from 'react';

export const useWebSocket = (workflowId) => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!workflowId) return;

    // For now, use polling instead of WebSocket
    // WebSocket would require additional AWS infrastructure
    const pollInterval = setInterval(async () => {
      try {
        // This would poll the API for status updates
        // Implementation depends on your backend setup
        console.log(`Polling status for workflow: ${workflowId}`);
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);

    setConnectionState('connected');

    return () => {
      clearInterval(pollInterval);
      setConnectionState('disconnected');
    };
  }, [workflowId]);

  return {
    connectionState,
    lastMessage,
  };
};

export default useWebSocket;
