/**
 * Simple app store using React context + useReducer.
 * Manages connection state, active screen, and cached data.
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { anubisClient, AnubisConfig } from '@/api/client';

export interface AppState {
  config: AnubisConfig | null;
  isConfigured: boolean;
  isConnecting: boolean;
  isConnected: boolean;
  error: string | null;
  notifications: number;  // unread count
  telemetryActive: boolean;
}

type Action =
  | { type: 'SET_CONFIG'; config: AnubisConfig | null }
  | { type: 'SET_CONNECTING'; value: boolean }
  | { type: 'SET_CONNECTED'; value: boolean }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'SET_NOTIFICATIONS'; count: number }
  | { type: 'SET_TELEMETRY'; active: boolean };

const initialState: AppState = {
  config: null,
  isConfigured: false,
  isConnecting: false,
  isConnected: false,
  error: null,
  notifications: 0,
  telemetryActive: false,
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_CONFIG':
      return { ...state, config: action.config, isConfigured: !!action.config };
    case 'SET_CONNECTING':
      return { ...state, isConnecting: action.value };
    case 'SET_CONNECTED':
      return { ...state, isConnected: action.value, error: action.value ? null : state.error };
    case 'SET_ERROR':
      return { ...state, error: action.error, isConnected: false };
    case 'SET_NOTIFICATIONS':
      return { ...state, notifications: action.count };
    case 'SET_TELEMETRY':
      return { ...state, telemetryActive: action.active };
    default:
      return state;
  }
}

interface AppContextValue extends AppState {
  init: () => Promise<void>;
  connect: (serverUrl: string, apiKey: string) => Promise<boolean>;
  registerDevice: (name: string) => Promise<boolean>;
  disconnect: () => Promise<void>;
  refreshNotifications: () => Promise<void>;
  setTelemetry: (active: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const init = useCallback(async () => {
    const config = await anubisClient.loadConfig();
    if (config && config.serverUrl && config.apiKey) {
      dispatch({ type: 'SET_CONFIG', config });
      // Test connection
      try {
        dispatch({ type: 'SET_CONNECTING', value: true });
        await anubisClient.health();
        dispatch({ type: 'SET_CONNECTED', value: true });
      } catch (err: any) {
        dispatch({ type: 'SET_ERROR', error: err.message });
      } finally {
        dispatch({ type: 'SET_CONNECTING', value: false });
      }
    }
  }, []);

  const connect = useCallback(async (serverUrl: string, apiKey: string): Promise<boolean> => {
    dispatch({ type: 'SET_CONNECTING', value: true });
    dispatch({ type: 'SET_ERROR', error: null });
    try {
      await anubisClient.saveConfig({ serverUrl, apiKey });
      await anubisClient.health();
      dispatch({ type: 'SET_CONNECTED', value: true });
      const config = await anubisClient.loadConfig();
      dispatch({ type: 'SET_CONFIG', config });
      return true;
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', error: err.message });
      return false;
    } finally {
      dispatch({ type: 'SET_CONNECTING', value: false });
    }
  }, []);

  const registerDevice = useCallback(async (name: string): Promise<boolean> => {
    try {
      await anubisClient.registerDevice(name);
      const config = await anubisClient.loadConfig();
      dispatch({ type: 'SET_CONFIG', config });
      return true;
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', error: err.message });
      return false;
    }
  }, []);

  const disconnect = useCallback(async () => {
    await anubisClient.clearConfig();
    dispatch({ type: 'SET_CONFIG', config: null });
    dispatch({ type: 'SET_CONNECTED', value: false });
  }, []);

  const refreshNotifications = useCallback(async () => {
    if (!anubisClient.isConfigured) return;
    const deviceId = anubisClient.deviceIdValue;
    if (!deviceId) return;
    try {
      const result = await anubisClient.getNotifications(deviceId);
      dispatch({ type: 'SET_NOTIFICATIONS', count: result.count });
    } catch {
      // silent — notification polling is best-effort
    }
  }, []);

  const setTelemetry = useCallback((active: boolean) => {
    dispatch({ type: 'SET_TELEMETRY', active });
  }, []);

  // Initialize on mount
  useEffect(() => { init(); }, [init]);

  // Poll notifications every 30s when connected
  useEffect(() => {
    if (!state.isConnected) return;
    refreshNotifications();
    const interval = setInterval(refreshNotifications, 30000);
    return () => clearInterval(interval);
  }, [state.isConnected, refreshNotifications]);

  const value: AppContextValue = {
    ...state,
    init,
    connect,
    registerDevice,
    disconnect,
    refreshNotifications,
    setTelemetry,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
