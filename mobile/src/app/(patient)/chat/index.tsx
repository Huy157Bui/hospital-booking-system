// src/app/(patient)/chat/index.tsx
import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity, 
  ActivityIndicator, Alert // ✅ Chỉ giữ lại các component cơ bản
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context'; // ✅ Import đúng thư viện có prop 'edges'
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { chatService } from '../../../services/chatService'; 
import { ChatSession } from '../../../types/chat';
import { useAuthStore } from '../../../store/useAuthStore';

export default function PatientChatListScreen() {
  const router = useRouter();
  const { token } = useAuthStore();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    if (!token) {
      router.replace('/(auth)/login');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await chatService.getMySessions();
      setSessions(data);
    } catch (err: any) {
      console.error('Load chat sessions error:', err);
      setError('Không thể kết nối. Vui lòng kiểm tra mạng hoặc thử lại.');
    } finally {
      setLoading(false);
    }
  }, [token, router]);

  useFocusEffect(
    useCallback(() => {
      loadSessions();
    }, [loadSessions])
  );

  const handleCreateNewSession = async () => {
    try {
      const newSession = await chatService.createSession();
      router.push({
        pathname: '/(patient)/chat/[sessionId]',
        params: { sessionId: String(newSession.id) },
      });
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể tạo phiên chat mới.');
    }
  };

  const handlePressSession = (sessionId: number) => {
    router.push({
      pathname: '/(patient)/chat/[sessionId]',
      params: { sessionId: String(sessionId) },
    });
  };

  if (loading && sessions.length === 0) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#2f6fed" />
          <Text style={styles.loadingText}>Đang tải lịch sử chat...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Trợ lý AI</Text>
      </View>

      {error ? (
        // ✅ GIAO DIỆN KHI CÓ LỖI MẠNG, CÓ NÚT THỬ LẠI
        <View style={styles.center}>
          <Ionicons name="wifi-outline" size={48} color="#9ca3af" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadSessions}>
            <Ionicons name="refresh" size={20} color="#fff" style={{ marginRight: 8 }} />
            <Text style={styles.retryButtonText}>Thử lại</Text>
          </TouchableOpacity>
        </View>
      ) : sessions.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="chatbubble-ellipses-outline" size={48} color="#cbd5e1" />
          <Text style={styles.emptyText}>Bạn chưa có phiên chat nào.</Text>
          <TouchableOpacity style={styles.createButton} onPress={handleCreateNewSession}>
            <Text style={styles.createButtonText}>+ Tạo phiên mới</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.sessionItem}
              onPress={() => handlePressSession(item.id)}
            >
              <View style={styles.sessionIcon}>
                <Ionicons name="chatbubble-ellipses" size={20} color="#2f6fed" />
              </View>
              <View style={styles.sessionInfo}>
                <Text style={styles.sessionTitle}>{item.title || 'Tư vấn sức khỏe'}</Text>
                <Text style={styles.sessionMeta}>
                  {new Date(item.updated_date || item.created_date).toLocaleString('vi-VN')}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#ccc" />
            </TouchableOpacity>
          )}
          contentContainerStyle={styles.listContent}
          // Cho phép kéo xuống để tải lại (Pull to refresh)
          onRefresh={loadSessions}
          refreshing={loading}
        />
      )}

      <TouchableOpacity style={styles.fab} onPress={handleCreateNewSession}>
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { paddingHorizontal: 20, paddingVertical: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee', marginBottom: 8 },
  headerTitle: { fontSize: 20, fontWeight: '700', color: '#333' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loadingText: { marginTop: 12, fontSize: 16, color: '#6b7280' },
  errorText: { marginTop: 12, fontSize: 16, color: '#ef4444', textAlign: 'center', marginBottom: 16 },
  retryButton: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#2f6fed', paddingVertical: 12, paddingHorizontal: 24, borderRadius: 8 },
  retryButtonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  emptyText: { fontSize: 16, color: '#888', marginBottom: 16 },
  createButton: { backgroundColor: '#2f6fed', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8 },
  createButtonText: { color: '#fff', fontWeight: '600' },
  listContent: { padding: 16 },
  sessionItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderRadius: 10, padding: 16, marginBottom: 10, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 2 },
  sessionIcon: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#e0e7ff', justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  sessionInfo: { flex: 1 },
  sessionTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
  sessionMeta: { fontSize: 12, color: '#888', marginTop: 4 },
  fab: { position: 'absolute', right: 20, bottom: 20, width: 56, height: 56, borderRadius: 28, backgroundColor: '#2f6fed', justifyContent: 'center', alignItems: 'center', elevation: 5, shadowColor: '#000', shadowOpacity: 0.3, shadowRadius: 5, shadowOffset: { width: 0, height: 2 } },
});