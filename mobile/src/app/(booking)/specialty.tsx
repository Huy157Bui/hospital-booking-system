// src/app/(booking)/specialty.tsx
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useSpecialties } from '../../hooks/useSpecialties';
import { useBookingStore } from '../../store/useBookingStore';

export default function BookingSpecialtyScreen() {
  const router = useRouter();
  const { setSpecialty } = useBookingStore();
  
  // Tái sử dụng hook đã viết, không cần fetch lại
  const { data: specialties, isLoading, isError, refetch } = useSpecialties();

  const handleSelectSpecialty = (id: number, name: string) => {
    // 1. Lưu vào store
    setSpecialty(id, name);
    // 2. Chuyển sang bước 2
    router.push('/(booking)/doctor');
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Không thể tải danh sách chuyên khoa.</Text>
        <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
          <Text style={styles.retryText}>Thử lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <FlatList
        data={specialties}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => handleSelectSpecialty(item.id, item.name)}
            activeOpacity={0.7}
          >
            <View style={styles.iconContainer}>
              <Ionicons name="medkit-outline" size={28} color="#2f6fed" />
            </View>
            <View style={styles.textContainer}>
              <Text style={styles.name}>{item.name}</Text>
              {item.description && (
                <Text style={styles.description} numberOfLines={2}>
                  {item.description}
                </Text>
              )}
            </View>
            <Ionicons name="chevron-forward" size={24} color="#ccc" />
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  listContainer: { padding: 16, gap: 12 },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  iconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  textContainer: { flex: 1 },
  name: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  description: { fontSize: 13, color: '#666', lineHeight: 18 },
  errorText: { color: '#c62828', marginBottom: 12, textAlign: 'center' },
  retryButton: { paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
});