import React from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, StyleSheet, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useBookingStore } from '../../store/useBookingStore';
import { useDoctorsBySpecialty } from '../../hooks/useDoctors';
import { Doctor } from '../../types/doctor';

export default function BookingDoctorScreen() {
  const router = useRouter();
  const { specialtyId, specialtyName, setDoctor } = useBookingStore();

  const { data: doctors, isLoading, isError, refetch } = useDoctorsBySpecialty(specialtyId);
  
  const handleSelectDoctor = (doctor: Doctor) => {
    const doctorName = (doctor as any).name || (doctor as any).user?.full_name || 'Bác sĩ';
    setDoctor(doctor.id, doctorName);
    router.push('/(booking)/slot');
  };

  if (!specialtyId) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Vui lòng chọn chuyên khoa trước.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryButton}>
          <Text style={styles.retryText}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
        <Text style={{ marginTop: 12, color: '#666' }}>Đang tải danh sách bác sĩ...</Text>
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Không thể tải danh sách bác sĩ.</Text>
        <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
          <Text style={styles.retryText}>Thử lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Bác sĩ chuyên khoa</Text>
        <Text style={styles.headerSubtitle}>{specialtyName || '...'}</Text>
      </View>

      <FlatList
        data={doctors}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>Chưa có bác sĩ nào trong chuyên khoa này.</Text>
          </View>
        }
        renderItem={({ item }) => {
          const name = item.full_name || item.user?.full_name || 'Bác sĩ';
          const avatar = item.avatar || item.user?.avatar;
          const degree = item.degree || 'Bác sĩ';
          const fee = item.consultation_fee || 0;

          return (
            <TouchableOpacity
              style={styles.card}
              onPress={() => handleSelectDoctor(item)}
              activeOpacity={0.7}
            >
              <View style={styles.avatarContainer}>
                {avatar ? (
                  <Image source={{ uri: avatar }} style={{ width: 48, height: 48, borderRadius: 24 }} />
                ) : (
                  <Ionicons name="person-circle" size={48} color="#2f6fed" />
                )}
              </View>
              <View style={styles.infoContainer}>
                <Text style={styles.doctorName}>{name}</Text>
                <Text style={styles.doctorDegree}>{degree}</Text>
                <View style={styles.feeContainer}>
                  <Ionicons name="cash-outline" size={16} color="#2f6fed" />
                  <Text style={styles.feeText}>
                    {Number(fee).toLocaleString('vi-VN')} đ / lượt khám
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#ccc" />
            </TouchableOpacity>
          );
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: { fontSize: 14, color: '#666', marginBottom: 4 },
  headerSubtitle: { fontSize: 18, fontWeight: 'bold', color: '#2f6fed' },
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
  avatarContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  infoContainer: { flex: 1 },
  doctorName: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  doctorDegree: { fontSize: 13, color: '#666', marginBottom: 8 },
  feeContainer: { flexDirection: 'row', alignItems: 'center' },
  feeText: { fontSize: 14, fontWeight: '600', color: '#2f6fed', marginLeft: 4 },
  emptyText: { fontSize: 14, color: '#888', textAlign: 'center' },
  errorText: { color: '#c62828', marginBottom: 12, textAlign: 'center', fontSize: 15 },
  retryButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
});