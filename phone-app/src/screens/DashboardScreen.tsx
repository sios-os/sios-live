/**
 * Dashboard screen — ANUBIS system status at a glance.
 * Shows threats, cameras, network, perception, and remote monitor status.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, RefreshControl, TouchableOpacity, StyleSheet,
} from 'react-native';
import { anubisClient, SystemStatus, Threat } from '@/api/client';
import { colors, spacing, fontSize, radius, shadow } from '@/theme/theme';

export function DashboardScreen() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [threats, setThreats] = useState<Threat[]>([]);
  const [cameras, setCameras] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, t, c] = await Promise.all([
        anubisClient.getSystemStatus(),
        anubisClient.getActiveThreats(),
        anubisClient.getCameras(),
      ]);
      setStatus(s);
      setThreats(t.threats || []);
      setCameras(c.cameras || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const severityColor = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case 'critical': return colors.urgent;
      case 'high': return colors.red;
      case 'medium': return colors.orange;
      case 'low': return colors.blue;
      default: return colors.textDim;
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={refresh} tintColor={colors.gold} />}
    >
      {error && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>Connection error: {error}</Text>
        </View>
      )}

      {/* Active Threats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Threats</Text>
        {threats.length === 0 ? (
          <View style={styles.okCard}>
            <Text style={styles.okText}>No active threats</Text>
          </View>
        ) : (
          threats.map(t => (
            <View key={t.threat_id} style={styles.threatCard}>
              <View style={[styles.threatBar, { backgroundColor: severityColor(t.severity) }]} />
              <View style={styles.threatBody}>
                <Text style={styles.threatType}>{t.type}</Text>
                <Text style={styles.threatDesc}>{t.description}</Text>
                <Text style={styles.threatTime}>
                  {new Date(t.timestamp * 1000).toLocaleString()}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>

      {/* System Status */}
      {status && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Status</Text>
          <StatusRow label="API Server" value={formatStatus(status.api_server)} />
          {status.perception && <StatusRow label="Perception" value={formatStatus(status.perception)} />}
          {status.cameras && <StatusRow label="Cameras" value={formatStatus(status.cameras)} />}
          {status.network && <StatusRow label="Network" value={formatStatus(status.network)} />}
          {status.remote_monitor && <StatusRow label="Remote Monitor" value={formatStatus(status.remote_monitor)} />}
          {status.messaging && <StatusRow label="Messaging" value={formatStatus(status.messaging)} />}
        </View>
      )}

      {/* Cameras */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Cameras ({cameras.length})</Text>
        {cameras.length === 0 ? (
          <Text style={styles.emptyText}>No cameras configured</Text>
        ) : (
          cameras.map(c => (
            <View key={c.camera_id} style={styles.cameraRow}>
              <View style={[styles.cameraDot, { backgroundColor: c.status === 'online' ? colors.green : colors.textMuted }]} />
              <Text style={styles.cameraName}>{c.name}</Text>
              <Text style={styles.cameraType}>{c.camera_type}</Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

function formatStatus(s: any): string {
  if (!s || typeof s !== 'object') return 'unknown';
  if (s.error) return 'error';
  if (s.status === 'healthy' || s.status === 'active' || s.status === 'running') return 'online';
  if (s.is_available !== undefined) return s.is_available ? 'available' : 'offline';
  if (s.total_cameras !== undefined) return `${s.total_cameras} cameras`;
  if (s.total_devices !== undefined) return `${s.total_devices} devices`;
  if (s.signal_available !== undefined) return s.signal_available ? 'signal' : 'email';
  return 'online';
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statusRow}>
      <Text style={styles.statusLabel}>{label}</Text>
      <Text style={[styles.statusValue, { color: value === 'error' ? colors.red : value === 'offline' ? colors.orange : colors.green }]}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  section: { padding: spacing.md },
  sectionTitle: {
    fontSize: fontSize.lg,
    fontWeight: 'bold',
    color: colors.gold,
    marginBottom: spacing.sm,
  },
  errorCard: {
    backgroundColor: '#3a1515',
    borderRadius: radius.md,
    padding: spacing.md,
    margin: spacing.md,
  },
  errorText: { color: colors.red, fontSize: fontSize.sm },
  okCard: {
    backgroundColor: '#15251a',
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  okText: { color: colors.green, fontSize: fontSize.md },
  threatCard: {
    flexDirection: 'row',
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    marginBottom: spacing.sm,
    overflow: 'hidden',
  },
  threatBar: { width: 4 },
  threatBody: { flex: 1, padding: spacing.md },
  threatType: { color: colors.text, fontSize: fontSize.md, fontWeight: 'bold' },
  threatDesc: { color: colors.textDim, fontSize: fontSize.sm, marginTop: 2 },
  threatTime: { color: colors.textMuted, fontSize: fontSize.xs, marginTop: 4 },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.bgCard,
    borderRadius: radius.sm,
    marginBottom: 4,
  },
  statusLabel: { color: colors.textDim, fontSize: fontSize.sm },
  statusValue: { fontSize: fontSize.sm, fontWeight: 'bold' },
  cameraRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.bgCard,
    borderRadius: radius.sm,
    marginBottom: 4,
  },
  cameraDot: { width: 8, height: 8, borderRadius: 4, marginRight: spacing.sm },
  cameraName: { color: colors.text, fontSize: fontSize.sm, flex: 1 },
  cameraType: { color: colors.textDim, fontSize: fontSize.xs },
  emptyText: { color: colors.textMuted, fontSize: fontSize.sm, padding: spacing.sm },
});
