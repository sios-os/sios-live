/**
 * Chat screen — talk to DEMON (ANUBIS's communicator).
 * Messages are sent via the API /api/chat endpoint.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { anubisClient } from '@/api/client';
import { colors, spacing, fontSize, radius } from '@/theme/theme';

interface Message {
  id: string;
  role: 'user' | 'anubis' | 'error';
  text: string;
  timestamp: number;
}

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    // Greeting
    setMessages([{
      id: 'greeting',
      role: 'anubis',
      text: "Hey Creator. I'm DEMON. What can I do for you?",
      timestamp: Date.now(),
    }]);
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      text,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);
    try {
      const result = await anubisClient.chat(text);
      const anubisMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'anubis',
        text: result.response || '(no response)',
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, anubisMsg]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: `e-${Date.now()}`,
        role: 'error',
        text: `Error: ${err.message}`,
        timestamp: Date.now(),
      }]);
    } finally {
      setSending(false);
    }
  }, [input, sending]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    const isError = item.role === 'error';
    return (
      <View style={[styles.msgRow, isUser ? styles.msgRowUser : styles.msgRowAnubis]}>
        <View style={[
          styles.msgBubble,
          isUser ? styles.bubbleUser : isError ? styles.bubbleError : styles.bubbleAnubis,
        ]}>
          {!isUser && !isError && <Text style={styles.msgSender}>DEMON</Text>}
          <Text style={[styles.msgText, isUser ? styles.textUser : styles.textAnubis]}>
            {item.text}
          </Text>
          <Text style={styles.msgTime}>
            {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
      keyboardVerticalOffset={90}
    >
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        onLayout={() => flatListRef.current?.scrollToEnd({ animated: false })}
      />
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Message DEMON..."
          placeholderTextColor={colors.textMuted}
          value={input}
          onChangeText={setInput}
          multiline
          maxLength={2000}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || sending) && styles.sendBtnDisabled]}
          onPress={send}
          disabled={!input.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator size="small" color={colors.bg} />
          ) : (
            <Text style={styles.sendText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  msgRow: { flexDirection: 'row', marginBottom: spacing.sm },
  msgRowUser: { justifyContent: 'flex-end' },
  msgRowAnubis: { justifyContent: 'flex-start' },
  msgBubble: {
    maxWidth: '80%',
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  bubbleUser: { backgroundColor: colors.gold, borderBottomRightRadius: radius.xs },
  bubbleAnubis: { backgroundColor: colors.bgCard, borderBottomLeftRadius: radius.xs },
  bubbleError: { backgroundColor: '#3a1515', borderBottomLeftRadius: radius.xs },
  msgSender: {
    fontSize: fontSize.xs,
    fontWeight: 'bold',
    color: colors.gold,
    marginBottom: 2,
  },
  msgText: { fontSize: fontSize.md, lineHeight: 20 },
  textUser: { color: colors.bg },
  textAnubis: { color: colors.text },
  msgTime: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  inputBar: {
    flexDirection: 'row',
    padding: spacing.sm,
    backgroundColor: colors.bgCard,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    backgroundColor: colors.bgInput,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: fontSize.md,
    color: colors.text,
    maxHeight: 100,
    marginRight: spacing.sm,
  },
  sendBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    justifyContent: 'center',
  },
  sendBtnDisabled: { opacity: 0.4 },
  sendText: { fontSize: fontSize.md, fontWeight: 'bold', color: colors.bg },
});
