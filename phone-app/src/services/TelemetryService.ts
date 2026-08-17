/**
 * Telemetry service — background data collection and transmission.
 *
 * Uses react-native-background-actions to run as a foreground service
 * on Android. Collects:
 *   - GPS location (for remote monitoring)
 *   - Accelerometer data (for fall detection)
 *   - Health data (heart rate, steps — from device sensors if available)
 *   - Battery status
 *
 * Sends data to ANUBIS at the configured interval.
 * Fall detection runs locally — if a sudden impact is detected,
 * an immediate alert is sent.
 */

import BackgroundService from 'react-native-background-actions';
import Geolocation from '@react-native-community/geolocation';
import { SensorServices, Accelerometer } from 'react-native-sensors';
import DeviceInfo from 'react-native-device-info';
import { anubisClient } from '@/api/client';

export interface TelemetryConfig {
  location: boolean;
  accelerometer: boolean;
  health: boolean;
  battery: boolean;
  intervalSec: number;
}

const FALL_THRESHOLD = 25.0;       // m/s² — sudden impact
const FALL_QUIET_PERIOD = 5000;    // ms — avoid duplicate alerts
const STATIONARY_THRESHOLD = 1.0;  // m/s² — no movement

class TelemetryServiceImpl {
  private config: TelemetryConfig | null = null;
  private accelerometerSubscription: any = null;
  private lastFallAlert: number = 0;
  private lastAccel: { x: number; y: number; z: number } = { x: 0, y: 0, z: 0 };
  private running: boolean = false;

  get isRunning(): boolean {
    return this.running;
  }

  async start(config: TelemetryConfig): Promise<void> {
    if (this.running) return;
    this.config = config;
    this.running = true;

    // Start accelerometer listener (high frequency for fall detection)
    if (config.accelerometer) {
      this.startAccelerometer();
    }

    // Start background task for periodic telemetry
    const taskName = 'ANUBISTelemetry';
    const taskTitle = 'ANUBIS Companion';
    const taskText = 'Sending telemetry to ANUBIS...';
    const taskColor = '#d4af37';

    const task = async () => {
      while (this.running) {
        try {
          await this.collectAndSend();
        } catch (err) {
          // silent — telemetry is best-effort
        }
        // Sleep for the configured interval
        await this.sleep(this.config?.intervalSec ?? 30);
      }
    };

    const options = {
      taskName,
      taskTitle,
      taskText,
      taskColor,
      linkingURI: 'anubis://companion',
    };

    try {
      await BackgroundService.start(task, options);
    } catch (err) {
      // Background actions may not be available in all environments
      // Fall back to simple interval
      this.running = true;
      setInterval(() => { if (this.running) this.collectAndSend().catch(() => {}); }, (config.intervalSec ?? 30) * 1000);
    }
  }

  async stop(): Promise<void> {
    this.running = false;
    if (this.accelerometerSubscription) {
      this.accelerometerSubscription.unsubscribe();
      this.accelerometerSubscription = null;
    }
    try {
      await BackgroundService.stop();
    } catch {
      // silent
    }
  }

  private startAccelerometer(): void {
    try {
      this.accelerometerSubscription = Accelerometer.subscribe(({ x, y, z }) => {
        this.lastAccel = { x, y, z };
        // Fall detection: compute total magnitude
        const magnitude = Math.sqrt(x * x + y * y + z * z);
        const now = Date.now();
        if (magnitude > FALL_THRESHOLD && (now - this.lastFallAlert) > FALL_QUIET_PERIOD) {
          this.lastFallAlert = now;
          this.onFallDetected(magnitude);
        }
      });
    } catch {
      // Sensors not available — skip
    }
  }

  private async onFallDetected(magnitude: number): Promise<void> {
    try {
      // Send immediate accelerometer data
      await anubisClient.sendAccelerometer(this.lastAccel.x, this.lastAccel.y, this.lastAccel.z);
      // Send a telemetry event marking this as a fall
      await anubisClient.sendTelemetry({
        type: 'fall_detected',
        magnitude,
        timestamp: Date.now() / 1000,
        accel: this.lastAccel,
      });
    } catch {
      // silent
    }
  }

  private async collectAndSend(): Promise<void> {
    if (!this.config || !anubisClient.isConfigured) return;

    const tasks: Promise<any>[] = [];

    // Battery status
    if (this.config.battery) {
      tasks.push(this.sendBattery());
    }

    // GPS location
    if (this.config.location) {
      tasks.push(this.sendLocation());
    }

    // Health data (if available from device sensors)
    if (this.config.health) {
      tasks.push(this.sendHealth());
    }

    // Heartbeat
    tasks.push(this.sendHeartbeat());

    await Promise.allSettled(tasks);
  }

  private async sendBattery(): Promise<void> {
    try {
      const batteryLevel = await DeviceInfo.getBatteryLevel();
      const isCharging = await DeviceInfo.isBatteryCharging();
      await anubisClient.sendPhoneStatus(
        Math.round(batteryLevel * 100),
        isCharging,
      );
    } catch {
      // silent
    }
  }

  private async sendLocation(): Promise<void> {
    return new Promise((resolve) => {
      try {
        Geolocation.getCurrentPosition(
          async (position) => {
            try {
              await anubisClient.sendLocation(
                position.coords.latitude,
                position.coords.longitude,
                position.coords.accuracy || 0,
                position.coords.speed || 0,
                position.coords.altitude || 0,
              );
            } catch { /* silent */ }
            resolve();
          },
          () => resolve(),  // silent — location may be denied
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
        );
      } catch {
        resolve();
      }
    });
  }

  private async sendHealth(): Promise<void> {
    try {
      // Health data requires platform-specific APIs (Google Fit / HealthKit)
      // For now, send steps=0 as a heartbeat. A native module can be added
      // later to read from Google Fit.
      await anubisClient.sendHealth(0, 0, 0, 0, 0);
    } catch {
      // silent
    }
  }

  private async sendHeartbeat(): Promise<void> {
    try {
      const batteryLevel = await DeviceInfo.getBatteryLevel();
      const isCharging = await DeviceInfo.isBatteryCharging();
      await anubisClient.heartbeat(
        Math.round(batteryLevel * 100),
        isCharging,
      );
    } catch {
      // silent
    }
  }

  private sleep(seconds: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, seconds * 1000));
  }
}

export const TelemetryService = new TelemetryServiceImpl();
