/**
 * ANUBIS API client — communicates with the ANUBIS API server.
 *
 * All endpoints require the API key in the Authorization header.
 * The server URL and API key are stored in AsyncStorage after setup.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  SERVER_URL: '@anubis/server_url',
  API_KEY: '@anubis/api_key',
  DEVICE_ID: '@anubis/device_id',
  DEVICE_TOKEN: '@anubis/device_token',
  DEVICE_NAME: '@anubis/device_name',
};

export interface AnubisConfig {
  serverUrl: string;
  apiKey: string;
  deviceId: string;
  deviceToken: string;
  deviceName: string;
}

export interface ChatResponse {
  response: string;
  error?: string;
}

export interface SystemStatus {
  timestamp: number;
  api_server: any;
  perception?: any;
  cameras?: any;
  threats?: any;
  network?: any;
  remote_monitor?: any;
  messaging?: any;
  [key: string]: any;
}

export interface Threat {
  threat_id: string;
  type: string;
  severity: string;
  description: string;
  timestamp: number;
  resolved: boolean;
}

export interface CameraInfo {
  camera_id: string;
  name: string;
  camera_type: string;
  status: string;
}

export interface Notification {
  notif_id: string;
  device_id: string;
  title: string;
  body: string;
  priority: string;
  created_at: number;
  delivered: boolean;
  action: string;
}

export interface DeviceInfo {
  device_id: string;
  name: string;
  owner: string;
  platform: string;
  status: string;
  registered_at: number;
  last_seen: number;
  battery_level: number;
  battery_charging: boolean;
}

class AnubisClient {
  private serverUrl: string = '';
  private apiKey: string = '';
  private deviceId: string = '';
  private deviceToken: string = '';

  /** Load saved configuration from AsyncStorage. */
  async loadConfig(): Promise<AnubisConfig | null> {
    try {
      const [serverUrl, apiKey, deviceId, deviceToken, deviceName] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEYS.SERVER_URL),
        AsyncStorage.getItem(STORAGE_KEYS.API_KEY),
        AsyncStorage.getItem(STORAGE_KEYS.DEVICE_ID),
        AsyncStorage.getItem(STORAGE_KEYS.DEVICE_TOKEN),
        AsyncStorage.getItem(STORAGE_KEYS.DEVICE_NAME),
      ]);
      if (!serverUrl || !apiKey) return null;
      this.serverUrl = serverUrl;
      this.apiKey = apiKey;
      this.deviceId = deviceId || '';
      this.deviceToken = deviceToken || '';
      return { serverUrl, apiKey, deviceId: deviceId || '', deviceToken: deviceToken || '', deviceName: deviceName || '' };
    } catch {
      return null;
    }
  }

  /** Save configuration to AsyncStorage. */
  async saveConfig(config: Partial<AnubisConfig>): Promise<void> {
    const tasks: [string, string][] = [];
    if (config.serverUrl !== undefined) {
      this.serverUrl = config.serverUrl;
      tasks.push([STORAGE_KEYS.SERVER_URL, config.serverUrl]);
    }
    if (config.apiKey !== undefined) {
      this.apiKey = config.apiKey;
      tasks.push([STORAGE_KEYS.API_KEY, config.apiKey]);
    }
    if (config.deviceId !== undefined) {
      this.deviceId = config.deviceId;
      tasks.push([STORAGE_KEYS.DEVICE_ID, config.deviceId]);
    }
    if (config.deviceToken !== undefined) {
      this.deviceToken = config.deviceToken;
      tasks.push([STORAGE_KEYS.DEVICE_TOKEN, config.deviceToken]);
    }
    if (config.deviceName !== undefined) {
      tasks.push([STORAGE_KEYS.DEVICE_NAME, config.deviceName]);
    }
    await Promise.all(tasks.map(([k, v]) => AsyncStorage.setItem(k, v)));
  }

  /** Clear all stored configuration. */
  async clearConfig(): Promise<void> {
    await AsyncStorage.multiRemove(Object.values(STORAGE_KEYS));
    this.serverUrl = '';
    this.apiKey = '';
    this.deviceId = '';
    this.deviceToken = '';
  }

  get isConfigured(): boolean {
    return !!this.serverUrl && !!this.apiKey;
  }

  get deviceIdValue(): string {
    return this.deviceId;
  }

  /** Core request method. */
  private async request<T = any>(
    path: string,
    method: 'GET' | 'POST' | 'PUT' = 'GET',
    body?: any,
  ): Promise<T> {
    if (!this.serverUrl || !this.apiKey) {
      throw new Error('Not configured — set server URL and API key first');
    }
    const url = `${this.serverUrl.replace(/\/$/, '')}${path}`;
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
    };
    const opts: RequestInit = { method, headers };
    if (body !== undefined) opts.body = JSON.stringify(body);

    const response = await fetch(url, opts);
    const text = await response.text();
    let data: any;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    if (!response.ok) {
      throw new Error(data.error || data.raw || `HTTP ${response.status}`);
    }
    return data as T;
  }

  // ===========================================================
  // SYSTEM
  // ===========================================================

  async health(): Promise<{ status: string; timestamp: number }> {
    return this.request('/api/health');
  }

  async getSystemStatus(): Promise<SystemStatus> {
    return this.request('/api/status');
  }

  // ===========================================================
  // CHAT
  // ===========================================================

  async chat(message: string): Promise<ChatResponse> {
    return this.request('/api/chat', 'POST', { message });
  }

  async speak(text: string, priority: string = 'normal'): Promise<{ request_id: string; status: string }> {
    return this.request('/api/speak', 'POST', { text, priority });
  }

  // ===========================================================
  // CAMERAS
  // ===========================================================

  async getCameras(): Promise<{ cameras: CameraInfo[] }> {
    return this.request('/api/cameras');
  }

  async captureFrame(cameraId: string): Promise<any> {
    return this.request(`/api/cameras/${cameraId}/frame`, 'POST');
  }

  async monitorAllCameras(): Promise<{ frames: any[] }> {
    return this.request('/api/cameras/monitor', 'POST');
  }

  // ===========================================================
  // THREATS
  // ===========================================================

  async getActiveThreats(): Promise<{ threats: Threat[] }> {
    return this.request('/api/threats');
  }

  async getThreatHistory(limit: number = 50): Promise<{ threats: Threat[] }> {
    return this.request(`/api/threats/history?limit=${limit}`);
  }

  async resolveThreat(threatId: string, resolution: string): Promise<{ status: string }> {
    return this.request('/api/threats/resolve', 'POST', { threat_id: threatId, resolution });
  }

  // ===========================================================
  // NOTIFICATIONS
  // ===========================================================

  async getNotifications(deviceId: string): Promise<{ notifications: Notification[]; count: number }> {
    return this.request(`/api/notifications?device_id=${encodeURIComponent(deviceId)}`);
  }

  async markNotificationDelivered(notifId: string): Promise<{ status: string }> {
    return this.request('/api/notifications/delivered', 'POST', { notif_id: notifId });
  }

  // ===========================================================
  // PHONE PROTOCOL
  // ===========================================================

  async registerDevice(name: string, owner: string = 'creator', platform: string = 'android'): Promise<{
    device_id: string;
    name: string;
    token: string;
    status: string;
  }> {
    const result = await this.request('/api/phone/register', 'POST', { name, owner, platform });
    await this.saveConfig({ deviceId: result.device_id, deviceToken: result.token, deviceName: name });
    return result;
  }

  async heartbeat(batteryLevel: number, batteryCharging: boolean): Promise<{ status: string }> {
    if (!this.deviceId) throw new Error('Device not registered');
    return this.request('/api/phone/heartbeat', 'POST', {
      device_id: this.deviceId,
      battery_level: batteryLevel,
      battery_charging: batteryCharging,
    });
  }

  async sendTelemetry(data: Record<string, any>): Promise<{ status: string }> {
    if (!this.deviceId) throw new Error('Device not registered');
    return this.request('/api/phone/telemetry', 'POST', {
      device_id: this.deviceId,
      data,
    });
  }

  // ===========================================================
  // REMOTE MONITOR — telemetry endpoints
  // ===========================================================

  async sendLocation(lat: number, lon: number, accuracy: number = 0, speed: number = 0, altitude: number = 0): Promise<{ status: string }> {
    return this.request('/api/remote/location', 'POST', {
      latitude: lat,
      longitude: lon,
      accuracy,
      speed,
      altitude,
      timestamp: Date.now() / 1000,
      source: 'phone',
    });
  }

  async sendAccelerometer(x: number, y: number, z: number): Promise<{ status: string }> {
    return this.request('/api/remote/accel', 'POST', { x, y, z, timestamp: Date.now() / 1000 });
  }

  async sendHealth(heartRate: number, steps: number = 0, stressLevel: number = 0, bloodOxygen: number = 0, bodyTemp: number = 0): Promise<{ status: string }> {
    return this.request('/api/remote/health', 'POST', {
      heart_rate: heartRate,
      steps,
      stress_level: stressLevel,
      blood_oxygen: bloodOxygen,
      body_temperature: bodyTemp,
      timestamp: Date.now() / 1000,
    });
  }

  async sendPhoneStatus(batteryLevel: number, batteryCharging: boolean, networkType: string = '', screenOn: boolean = false): Promise<{ status: string }> {
    return this.request('/api/remote/phone', 'POST', {
      battery_level: batteryLevel,
      battery_charging: batteryCharging,
      network_type: networkType,
      screen_on: screenOn,
      timestamp: Date.now() / 1000,
    });
  }

  // ===========================================================
  // EMERGENCY
  // ===========================================================

  async sendEmergencyAlert(message: string): Promise<{ sent: any[] }> {
    return this.request('/api/emergency/alert', 'POST', { message });
  }

  // ===========================================================
  // CONTACTS
  // ===========================================================

  async getContacts(): Promise<{ contacts: any[] }> {
    return this.request('/api/contacts');
  }

  async addContact(name: string, phone: string, email: string = '', relationship: string = '', role: string = 'general'): Promise<any> {
    return this.request('/api/contacts', 'POST', { name, phone, email, relationship, role });
  }

  // ===========================================================
  // NETWORK
  // ===========================================================

  async getNetworkDevices(): Promise<{ devices: any[] }> {
    return this.request('/api/network/devices');
  }

  async getNetworkStatus(): Promise<any> {
    return this.request('/api/network/status');
  }

  // ===========================================================
  // SENSORY MODE
  // ===========================================================

  async setSensoryMode(mode: string): Promise<{ mode: string; status: string }> {
    return this.request(`/api/mode/${mode}`, 'POST');
  }
}

export const anubisClient = new AnubisClient();
export { STORAGE_KEYS };
