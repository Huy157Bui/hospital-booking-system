// src/app/patient/chat/index.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { chatService } from '../../../services/chatService';
import { ChatSession } from '../../../types/'; // giả sử có type

export default function PatientChatListScreen() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await chatService.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Load chat sessions error:', error);
      Alert.alert('Lỗi', 'Không thể tải danh sách chat.');
    } finally {
      setLoading(false);
    }
  };

  // Tải lại khi màn hình được focus (nếu quay lại từ session)
  useFocusEffect(
    useCallback(() => {
      loadSessions();
    }, [])
  );

  const handleCreateNewSession = async () => {
    try {
      const newSession = await chatService.createSession();
      router.push({
        pathname: '/patient/chat/[sessionId]',
        params: { sessionId: newSession.id },
      });
    } catch (error) {
      console.error('Create session error:', error);
      Alert.alert('Lỗi', 'Không thể tạo phiên chat mới.');
    }
  };

  const handlePressSession = (sessionId: string) => {
    router.push({
      pathname: '/patient/chat/[sessionId]',
      params: { sessionId },
    });
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {sessions.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>Bạn chưa có phiên chat nào.</Text>
          <TouchableOpacity style={styles.createButton} onPress={handleCreateNewSession}>
            <Text style={styles.createButtonText}>+ Tạo phiên mới</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.sessionItem}
              onPress={() => handlePressSession(item.id)}
            >
              <Text style={styles.sessionTitle}>{item.title || 'Tư vấn sức khỏe'}</Text>
              <Text style={styles.sessionMeta}>
                {new Date(item.updatedAt).toLocaleString('vi-VN')}
              </Text>
            </TouchableOpacity>
          )}
          contentContainerStyle={{ padding: 16 }}
        />
      )}

      {/* Nút tạo mới nổi */}
      <TouchableOpacity style={styles.fab} onPress={handleCreateNewSession}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { fontSize: 16, color: '#888', marginBottom: 16 },
  createButton: {
    backgroundColor: '#2f6fed',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  createButtonText: { color: '#fff', fontWeight: '600' },
  sessionItem: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sessionTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
  sessionMeta: { fontSize: 12, color: '#888', marginTop: 4 },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#2f6fed',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 5,
    shadowOffset: { width: 0, height: 2 },
  },
  fabText: { fontSize: 28, color: '#fff', fontWeight: '300' },
});