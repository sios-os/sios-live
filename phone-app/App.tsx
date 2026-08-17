/**
 * ANUBIS Companion App — main entry point.
 *
 * Tab navigation: Chat | Dashboard | Notifications | Settings
 * If not configured, shows the Setup screen first.
 */

import React from 'react';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppProvider, useApp } from '@/store/appStore';
import { SetupScreen } from '@/screens/SetupScreen';
import { ChatScreen } from '@/screens/ChatScreen';
import { DashboardScreen } from '@/screens/DashboardScreen';
import { NotificationsScreen } from '@/screens/NotificationsScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import { colors } from '@/theme/theme';

const Tab = createBottomTabNavigator();

const AnubisTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.bg,
    card: colors.bgCard,
    text: colors.text,
    border: colors.border,
    primary: colors.gold,
  },
};

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  // Simple text-based icons (vector icons can be added later)
  const icons: Record<string, string> = {
    Chat: '💬',
    Dashboard: '◈',
    Alerts: '🔔',
    Settings: '⚙',
  };
  return null; // Bottom tab navigator handles icons via options
}

function MainApp() {
  const { isConfigured, isConnected, isConnecting } = useApp();

  if (!isConfigured || !isConnected) {
    return <SetupScreen />;
  }

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.gold,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.bgCard,
          borderTopColor: colors.border,
          paddingBottom: 4,
        },
        headerStyle: { backgroundColor: colors.bgCard },
        headerTintColor: colors.gold,
        headerTitleStyle: { fontWeight: 'bold', letterSpacing: 1 },
      }}
    >
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{ title: 'DEMON' }}
      />
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: 'Status' }}
      />
      <Tab.Screen
        name="Alerts"
        component={NotificationsScreen}
        options={{ title: 'Alerts' }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <NavigationContainer theme={AnubisTheme}>
          <MainApp />
        </NavigationContainer>
      </AppProvider>
    </SafeAreaProvider>
  );
}
