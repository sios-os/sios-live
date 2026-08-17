/**
 * Notifications screen — view and acknowledge ANUBIS notifications.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, RefreshControl, TouchableOpacity, StyleSheet, Alert,
} from 'react-native';
import { anubisClient, Notification } from '@/api/client';
import { useApp } from '@/store/appStore';
import { colors, spacing, fontSize, radius } from '@/theme/theme';

export function NotificationsScreen() {
  const { refreshNotifications } = useApp();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const deviceId = anubisClient.deviceIdValue;
    if (!deviceId) { setLoading(false); return; }
    setLoading(true);
    try {
      const result = await anubisClient.getNotifications(deviceId);
      setNotifications(result.notifications || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDismiss = async (notif: Notification) => {
    try {
      await anubisClient.markNotificationDelivered(notif.notif_id);
      setNotifications(prev => prev.filter(n => n.notif_id !== notif.notif_id));
      refreshNotifications();
    } catch {
      Alert.alert('Error', 'Could not dismiss notification');
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return colors.urgent;
      case 'high': return colors.high;
      case 'normal': return colors.normal;
      default: return colors.low;
    }
  };

  const renderItem = ({ item }: { item: Notification }) => (
    <View style={styles.card}>
      <View style={[styles.priorityBar, { backgroundColor: priorityColor(item.priority) }]} />
      <View style={styles.cardBody}>
        <View style={styles.cardHeader}>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.priority}>{item.priority}</Text>
        </View>
        <Text style={styles.body}>{item.body}</Text>
        <Text style={styles.time}>
          {new Date(item.created_at * 1000).toLocaleString()}
        </Text>
        {item.action && (
          <Text style={styles.action}>Action: {item.action}</Text>
        )}
        <TouchableOpacity style={styles.dismissBtn} onPress={() => handleDismiss(item)}>
          <Text style={styles.dismissText}>Dismiss</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={notifications}
        renderItem={renderItem}
        keyExtractor={item => item.notif_id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={colors.gold} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No pending notifications</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  card: {
    flexDirection: 'row',
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    marginBottom: spacing.sm,
    overflow: 'hidden',
  },
  priorityBar: { width: 4 },
  cardBody: { flex: 1, padding: spacing.md },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: colors.text, fontSize: fontSize.lg, fontWeight: 'bold', flex: 1 },
  priority: { color: colors.textDim, fontSize: fontSize.xs, textTransform: 'uppercase' },
  body: { color: colors.text, fontSize: fontSize.md, marginTop: spacing.xs, lineHeight: 20 },
  time: { color: colors.textMuted, fontSize: fontSize.xs, marginTop: spacing.sm },
  action: { color: colors.gold, fontSize: fontSize.sm, marginTop: 4 },
  dismissBtn: {
    backgroundColor: colors.bgElevated,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    marginTop: spacing.sm,
    alignSelf: 'flex-start',
  },
  dismissText: { color: colors.textDim, fontSize: fontSize.sm },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: spacing.xxl },
  emptyText: { color: colors.textMuted, fontSize: fontSize.md },
});
