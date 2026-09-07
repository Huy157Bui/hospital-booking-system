import React from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, 
  ActivityIndicator, FlatList 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useAuthStore } from '../../../store/useAuthStore';
import { useSpecialties } from '../../../hooks/useSpecialties';
import { useBookingStore } from '../../../store/useBookingStore';

export default function PatientHomeScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { data: specialties, isLoading, isError, refetch } = useSpecialties();

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        
        {/* --- HEADER --- */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Xin chào,</Text>
            <Text style={styles.userName}>{user?.full_name || user?.full_name || 'Bệnh nhân'} 👋</Text>
          </View>
          <TouchableOpacity 
            style={styles.avatarContainer}
            onPress={() => router.push('/(patient)/profile')}
          >
            <Ionicons name="person-circle-outline" size={40} color="#2f6fed" />
          </TouchableOpacity>
        </View>

        {/* --- QUICK ACTIONS --- */}
        <View style={styles.actionContainer}>
          <TouchableOpacity 
            style={styles.actionCard} 
            onPress={() => router.push('/(booking)/specialty')}
          >
            <View style={[styles.iconBox, { backgroundColor: '#e3f2fd' }]}>
              <Ionicons name="calendar-clear-outline" size={28} color="#2f6fed" />
            </View>
            <Text style={styles.actionText}>Đặt lịch khám</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionCard} 
            onPress={() => router.push('/(patient)/chat')}
          >
            <View style={[styles.iconBox, { backgroundColor: '#f3e5f5' }]}>
              <Ionicons name="chatbubbles-outline" size={28} color="#9c27b0" />
            </View>
            <Text style={styles.actionText}>Hỏi AI tư vấn</Text>
          </TouchableOpacity>
        </View>

        {/* --- SPECIALTIES SECTION --- */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Chuyên khoa</Text>
          
          {isLoading && (
            <ActivityIndicator size="small" color="#2f6fed" style={{ marginTop: 20 }} />
          )}

          {isError && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>Không thể tải danh sách chuyên khoa.</Text>
              <TouchableOpacity onPress={() => refetch()}>
                <Text style={styles.retryText}>Thử lại</Text>
              </TouchableOpacity>
            </View>
          )}

          {!isLoading && !isError && specialties && (
            <FlatList
              data={specialties}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item) => String(item.id)}
              contentContainerStyle={{ paddingHorizontal: 20, gap: 12 }}
              renderItem={({ item }) => (
                <TouchableOpacity 
                  style={styles.specialtyCard}
                  onPress={() => {
                    useBookingStore.getState().setSpecialty(item.id, item.name);
                    router.push('/(booking)/doctor');
                  }}
                >
                  <View style={styles.specialtyIcon}>
                    <Ionicons name="medkit-outline" size={24} color="#fff" />
                  </View>
                  <Text style={styles.specialtyName} numberOfLines={2}>
                    {item.name}
                  </Text>
                </TouchableOpacity>
              )}
            />
          )}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  greeting: { fontSize: 16, color: '#666' },
  userName: { fontSize: 24, fontWeight: 'bold', color: '#333', marginTop: 4 },
  avatarContainer: {
    width: 48, height: 48, borderRadius: 24, backgroundColor: '#fff',
    justifyContent: 'center', alignItems: 'center',
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, elevation: 3,
  },
  actionContainer: { flexDirection: 'row', paddingHorizontal: 20, gap: 12, marginBottom: 24 },
  actionCard: {
    flex: 1, backgroundColor: '#fff', padding: 16, borderRadius: 16, alignItems: 'center',
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  iconBox: { width: 56, height: 56, borderRadius: 28, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  actionText: { fontSize: 14, fontWeight: '600', color: '#333', textAlign: 'center' },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 16, paddingHorizontal: 20 },
  specialtyCard: {
    width: 100, height: 120, backgroundColor: '#fff', borderRadius: 12, padding: 12,
    justifyContent: 'center', alignItems: 'center',
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 2, elevation: 1,
  },
  specialtyIcon: {
    width: 48, height: 48, borderRadius: 24, backgroundColor: '#2f6fed',
    justifyContent: 'center', alignItems: 'center', marginBottom: 8,
  },
  specialtyName: { fontSize: 13, fontWeight: '500', textAlign: 'center', color: '#333' },
  errorBox: { marginHorizontal: 20, padding: 16, backgroundColor: '#ffebee', borderRadius: 8, alignItems: 'center' },
  errorText: { color: '#c62828', marginBottom: 8 },
  retryText: { color: '#2f6fed', fontWeight: 'bold' },
});