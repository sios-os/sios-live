/**
 * Setup screen — first-time configuration.
 * User enters ANUBIS server URL and API key, then registers their device.
 */

import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView,
  KeyboardAvoidingView, Platform, Alert, ActivityIndicator,
} from 'react-native';
import { useApp } from '@/store/appStore';
import { colors, spacing, fontSize, radius, shadow } from '@/theme/theme';

export function SetupScreen() {
  const { connect, registerDevice } = useApp();
  const [step, setStep] = useState<'connect' | 'register' | 'done'>('connect');
  const [serverUrl, setServerUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    if (!serverUrl.trim() || !apiKey.trim()) {
      setError('Server URL and API key are required');
      return;
    }
    setLoading(true);
    setError(null);
    const ok = await connect(serverUrl.trim(), apiKey.trim());
    setLoading(false);
    if (ok) {
      setStep('register');
    } else {
      setError('Could not connect. Check the URL and API key, and ensure the ANUBIS API server is running.');
    }
  };

  const handleRegister = async () => {
    const name = deviceName.trim() || 'My Phone';
    setLoading(true);
    setError(null);
    const ok = await registerDevice(name);
    setLoading(false);
    if (ok) {
      setStep('done');
    } else {
      setError('Could not register device. The phone protocol may not be configured on the server.');
    }
  };

  if (step === 'done') {
    return (
      <View style={styles.container}>
        <View style={styles.card}>
          <Text style={styles.title}>Connected</Text>
          <Text style={styles.body}>
            Your phone is now paired with ANUBIS. Telemetry, notifications,
            and chat are active.
          </Text>
          <Text style={styles.hint}>
            You can now use the tabs below to chat, view status, and manage settings.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <Text style={styles.logo}>ANUBIS</Text>
          <Text style={styles.subtitle}>Sovereign Intelligence</Text>
        </View>

        {step === 'connect' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Connect to ANUBIS</Text>
            <Text style={styles.label}>Server URL</Text>
            <TextInput
              style={styles.input}
              placeholder="http://192.168.1.100:8765"
              placeholderTextColor={colors.textMuted}
              value={serverUrl}
              onChangeText={setServerUrl}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <Text style={styles.label}>API Key</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter your ANUBIS_API_KEY"
              placeholderTextColor={colors.textMuted}
              value={apiKey}
              onChangeText={setApiKey}
              autoCapitalize="none"
              autoCorrect={false}
              secureTextEntry
            />
            {error && <Text style={styles.errorText}>{error}</Text>}
            <TouchableOpacity
              style={styles.button}
              onPress={handleConnect}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={colors.bg} />
              ) : (
                <Text style={styles.buttonText}>Connect</Text>
              )}
            </TouchableOpacity>
            <Text style={styles.hint}>
              The server URL is the address of your ANUBIS API server.
              The API key is set by the ANUBIS_API_KEY environment variable.
            </Text>
          </View>
        )}

        {step === 'register' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Register Your Phone</Text>
            <Text style={styles.body}>
              Give your phone a name so ANUBIS can identify it.
            </Text>
            <Text style={styles.label}>Device Name</Text>
            <TextInput
              style={styles.input}
              placeholder="Storm Phone"
              placeholderTextColor={colors.textMuted}
              value={deviceName}
              onChangeText={setDeviceName}
            />
            {error && <Text style={styles.errorText}>{error}</Text>}
            <TouchableOpacity
              style={styles.button}
              onPress={handleRegister}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={colors.bg} />
              ) : (
                <Text style={styles.buttonText}>Register Device</Text>
              )}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: spacing.lg },
  header: { alignItems: 'center', marginBottom: spacing.xxl },
  logo: {
    fontSize: fontSize.title,
    fontWeight: 'bold',
    color: colors.gold,
    letterSpacing: 6,
  },
  subtitle: {
    fontSize: fontSize.sm,
    color: colors.textDim,
    letterSpacing: 3,
    marginTop: spacing.xs,
  },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: radius.lg,
    padding: spacing.lg,
    ...shadow.md,
  },
  cardTitle: {
    fontSize: fontSize.xl,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: fontSize.xxl,
    fontWeight: 'bold',
    color: colors.gold,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  body: {
    fontSize: fontSize.md,
    color: colors.text,
    marginBottom: spacing.md,
    lineHeight: 22,
  },
  label: {
    fontSize: fontSize.sm,
    color: colors.textDim,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  input: {
    backgroundColor: colors.bgInput,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
  },
  button: {
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    marginTop: spacing.lg,
  },
  buttonText: {
    fontSize: fontSize.lg,
    fontWeight: 'bold',
    color: colors.bg,
  },
  errorText: {
    fontSize: fontSize.sm,
    color: colors.red,
    marginTop: spacing.sm,
  },
  hint: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: spacing.md,
    lineHeight: 18,
  },
});
