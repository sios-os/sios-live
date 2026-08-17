/**
 * Settings screen — configure telemetry, privacy mode, and connection.
 */

import React, { useState, useEffect } from 'react';
import {
  View, Text, Switch, TouchableOpacity, StyleSheet, ScrollView, Alert,
} from 'react-native';
import { useApp } from '@/store/appStore';
import { anubisClient } from '@/api/client';
import { TelemetryService } from '@/services/TelemetryService';
import { colors, spacing, fontSize, radius } from '@/theme/theme';

export function SettingsScreen() {
  const { config, disconnect, setTelemetry, telemetryActive } = useApp();
  const [telemetryOn, setTelemetryOn] = useState(telemetryActive);
  const [locationOn, setLocationOn] = useState(true);
  const [accelerometerOn, setAccelerometerOn] = useState(true);
  const [healthOn, setHealthOn] = useState(true);
  const [batteryOn, setBatteryOn] = useState(true);
  const [sensoryMode, setSensoryMode] = useState('ambient');
  const [interval, setIntervalSec] = useState(30);

  const toggleTelemetry = async (value: boolean) => {
    setTelemetryOn(value);
    setTelemetry(value);
    if (value) {
      await TelemetryService.start({
        location: locationOn,
        accelerometer: accelerometerOn,
        health: healthOn,
        battery: batteryOn,
        intervalSec: interval,
      });
    } else {
      await TelemetryService.stop();
    }
  };

  const handleDisconnect = () => {
    Alert.alert(
      'Disconnect',
      'Remove ANUBIS connection? You will need to re-enter the server URL and API key.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Disconnect', style: 'destructive', onPress: () => {
          TelemetryService.stop();
          disconnect();
        }},
      ],
    );
  };

  const changeSensoryMode = async (mode: string) => {
    setSensoryMode(mode);
    try {
      await anubisClient.setSensoryMode(mode);
      Alert.alert('Mode Changed', `ANUBIS sensory mode set to: ${mode}`);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Connection info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Connection</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Server</Text>
          <Text style={styles.value}>{config?.serverUrl || 'Not set'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Device</Text>
          <Text style={styles.value}>{config?.deviceName || 'Not registered'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Device ID</Text>
          <Text style={styles.valueSmall}>{config?.deviceId || '—'}</Text>
        </View>
      </View>

      {/* Telemetry */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Telemetry</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Enable background telemetry</Text>
          <Switch
            value={telemetryOn}
            onValueChange={toggleTelemetry}
            trackColor={{ false: colors.border, true: colors.gold }}
            thumbColor={telemetryOn ? colors.goldBright : colors.textMuted}
          />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>GPS location</Text>
          <Switch
            value={locationOn}
            onValueChange={setLocationOn}
            disabled={!telemetryOn}
            trackColor={{ false: colors.border, true: colors.gold }}
            thumbColor={locationOn ? colors.goldBright : colors.textMuted}
          />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Accelerometer (fall detection)</Text>
          <Switch
            value={accelerometerOn}
            onValueChange={setAccelerometerOn}
            disabled={!telemetryOn}
            trackColor={{ false: colors.border, true: colors.gold }}
            thumbColor={accelerometerOn ? colors.goldBright : colors.textMuted}
          />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Health data (heart rate, steps)</Text>
          <Switch
            value={healthOn}
            onValueChange={setHealthOn}
            disabled={!telemetryOn}
            trackColor={{ false: colors.border, true: colors.gold }}
            thumbColor={healthOn ? colors.goldBright : colors.textMuted}
          />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Battery status</Text>
          <Switch
            value={batteryOn}
            onValueChange={setBatteryOn}
            disabled={!telemetryOn}
            trackColor={{ false: colors.border, true: colors.gold }}
            thumbColor={batteryOn ? colors.goldBright : colors.textMuted}
          />
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Update interval</Text>
          <Text style={styles.value}>{interval}s</Text>
        </View>
      </View>

      {/* Sensory mode */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ANUBIS Sensory Mode</Text>
        {['ambient', 'wake_word', 'conversation', 'privacy'].map(mode => (
          <TouchableOpacity
            key={mode}
            style={[styles.modeRow, sensoryMode === mode && styles.modeRowActive]}
            onPress={() => changeSensoryMode(mode)}
          >
            <Text style={[styles.modeText, sensoryMode === mode && styles.modeTextActive]}>
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </Text>
            {sensoryMode === mode && <Text style={styles.modeCheck}>✓</Text>}
          </TouchableOpacity>
        ))}
      </View>

      {/* Emergency */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Emergency</Text>
        <TouchableOpacity
          style={styles.emergencyBtn}
          onPress={() => {
            Alert.alert(
              'Emergency Alert',
              'Send an emergency alert to ANUBIS? This will trigger emergency notifications to your contacts.',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Send Alert', style: 'destructive', onPress: async () => {
                  try {
                    await anubisClient.sendEmergencyAlert('Emergency button pressed from phone app');
                    Alert.alert('Sent', 'Emergency alert has been sent.');
                  } catch (err: any) {
                    Alert.alert('Error', err.message);
                  }
                }},
              ],
            );
          }}
        >
          <Text style={styles.emergencyText}>Send Emergency Alert</Text>
        </TouchableOpacity>
      </View>

      {/* Disconnect */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.disconnectBtn} onPress={handleDisconnect}>
          <Text style={styles.disconnectText}>Disconnect from ANUBIS</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>ANUBIS Companion v1.0</Text>
        <Text style={styles.footerSub}>Sovereign Interactive Operating System</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  section: {
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    margin: spacing.md,
    padding: spacing.md,
  },
  sectionTitle: {
    fontSize: fontSize.lg,
    fontWeight: 'bold',
    color: colors.gold,
    marginBottom: spacing.md,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  label: { color: colors.text, fontSize: fontSize.md, flex: 1 },
  value: { color: colors.textDim, fontSize: fontSize.sm },
  valueSmall: { color: colors.textMuted, fontSize: fontSize.xs, maxWidth: 150 },
  modeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
    marginBottom: 4,
    backgroundColor: colors.bgInput,
  },
  modeRowActive: { backgroundColor: colors.goldDim + '30', borderWidth: 1, borderColor: colors.gold },
  modeText: { color: colors.textDim, fontSize: fontSize.md },
  modeTextActive: { color: colors.gold, fontSize: fontSize.md, fontWeight: 'bold' },
  modeCheck: { color: colors.gold, fontSize: fontSize.lg },
  emergencyBtn: {
    backgroundColor: colors.red,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  emergencyText: { color: '#fff', fontSize: fontSize.lg, fontWeight: 'bold' },
  disconnectBtn: {
    backgroundColor: colors.bgElevated,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  disconnectText: { color: colors.textDim, fontSize: fontSize.md },
  footer: { alignItems: 'center', padding: spacing.xl },
  footerText: { color: colors.textMuted, fontSize: fontSize.xs },
  footerSub: { color: colors.textMuted, fontSize: fontSize.xs, marginTop: 2 },
});
