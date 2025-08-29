import { useState, useEffect, useRef, useCallback } from 'react'
import { toast } from 'react-hot-toast'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  autoReconnect?: boolean
}

export const useWebSocket = (
  endpoint: string,
  options: UseWebSocketOptions = {}
) => {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    autoReconnect = true
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const isConnectingRef = useRef(false)

  // Build WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}${endpoint}`
  }, [endpoint])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    isConnectingRef.current = true
    setError(null)

    try {
      const wsUrl = getWebSocketUrl()
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setIsConnected(true)
        isConnectingRef.current = false
        reconnectAttemptsRef.current = 0
        onOpen?.()
        
        // Send initial ping
        sendMessage({ type: 'ping' })
        
        toast.success('Connected to BAC Hunter')
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Handle system messages
          if (message.type === 'pong') {
            // Heartbeat response - no action needed
            return
          }
          
          // Add message to state
          setMessages(prev => [...prev, message])
          
          // Call custom message handler
          onMessage?.(message)
          
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
          setError('Invalid message format')
        }
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        isConnectingRef.current = false
        
        // Only show toast if it wasn't a clean close
        if (!event.wasClean) {
          toast.error('Connection lost')
        }
        
        onClose?.()
        
        // Attempt to reconnect if auto-reconnect is enabled
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          
          reconnectTimeoutRef.current = setTimeout(() => {
            toast.info(`Reconnecting... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
            connect()
          }, reconnectInterval)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached')
          toast.error('Failed to reconnect after multiple attempts')
        }
      }

      ws.onerror = (event) => {
        isConnectingRef.current = false
        setError('WebSocket error occurred')
        onError?.(event)
        console.error('WebSocket error:', event)
      }

      wsRef.current = ws
      
    } catch (err) {
      isConnectingRef.current = false
      setError('Failed to create WebSocket connection')
      console.error('WebSocket connection error:', err)
    }
  }, [getWebSocketUrl, onOpen, onClose, onError, autoReconnect, reconnectInterval, maxReconnectAttempts])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect')
      wsRef.current = null
    }
    
    setIsConnected(false)
    isConnectingRef.current = false
    reconnectAttemptsRef.current = 0
  }, [])

  // Send message through WebSocket
  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message))
      } catch (err) {
        console.error('Failed to send WebSocket message:', err)
        setError('Failed to send message')
      }
    } else {
      console.warn('WebSocket is not connected')
      setError('Not connected to server')
    }
  }, [])

  // Subscribe to specific scan updates
  const subscribeToScan = useCallback((scanId: string) => {
    sendMessage({
      type: 'subscribe_scan',
      scan_id: scanId
    })
  }, [sendMessage])

  // Unsubscribe from scan updates
  const unsubscribeFromScan = useCallback((scanId: string) => {
    sendMessage({
      type: 'unsubscribe_scan',
      scan_id: scanId
    })
  }, [sendMessage])

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  // Get messages by type
  const getMessagesByType = useCallback((type: string) => {
    return messages.filter(msg => msg.type === type)
  }, [messages])

  // Get latest message of specific type
  const getLatestMessageByType = useCallback((type: string) => {
    const typeMessages = getMessagesByType(type)
    return typeMessages[typeMessages.length - 1] || null
  }, [getMessagesByType])

  // Manual reconnect
  const reconnect = useCallback(() => {
    disconnect()
    setTimeout(connect, 1000) // Wait 1 second before reconnecting
  }, [connect, disconnect])

  // Effect to connect on mount
  useEffect(() => {
    connect()
    
    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Effect to handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, can disconnect to save resources
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.close(1000, 'Page hidden')
        }
      } else {
        // Page is visible, reconnect if needed
        if (wsRef.current?.readyState !== WebSocket.OPEN && autoReconnect) {
          connect()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [connect, autoReconnect])

  // Effect to handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      if (!isConnected && autoReconnect) {
        toast.success('Network connection restored')
        connect()
      }
    }

    const handleOffline = () => {
      if (isConnected) {
        toast.error('Network connection lost')
        setIsConnected(false)
      }
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [isConnected, autoReconnect, connect])

  return {
    // State
    isConnected,
    messages,
    error,
    
    // Actions
    connect,
    disconnect,
    reconnect,
    sendMessage,
    subscribeToScan,
    unsubscribeFromScan,
    clearMessages,
    
    // Utilities
    getMessagesByType,
    getLatestMessageByType,
    
    // Connection info
    readyState: wsRef.current?.readyState,
    url: getWebSocketUrl()
  }
}