import React, { useState } from 'react';
import { 
  View, Text, FlatList, TouchableOpacity, StyleSheet, 
  ActivityIndicator, RefreshControl, TextInput 
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';

import { doctorService } from '../../../services/doctorService';
import { PatientSummary } from '../../../types/patient';

export default function DoctorPatientsScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: patients, isLoading, refetch, isRefetching } = useQuery<PatientSummary[]>({
    queryKey: ['doctor-patients'],
    queryFn: async () => {
      return await doctorService.getPatients();
    },
  });

  const filteredPatients = patients?.filter((p) => 
    p.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.phone && p.phone.includes(searchQuery))
  ) || [];

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Chưa có';
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  const renderItem = ({ item }: { item: PatientSummary }) => (
    <TouchableOpacity 
      style={styles.card}
      onPress={() => router.push({
        pathname: '/(doctor)/patient/[patientId]',
        params: { patientId: item.id.toString() }
      })} 
    >
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{item.full_name.charAt(0).toUpperCase()}</Text>
      </View>
      <View style={styles.info}>
        <Text style={styles.name}>{item.full_name}</Text>
        <Text style={styles.detail}>
          <Ionicons name="call-outline" size={14} color="#64748b" /> {item.phone || 'Chưa có SĐT'}
        </Text>
        <Text style={styles.detail}>
          <Ionicons name="time-outline" size={14} color="#64748b" /> Khám gần nhất: {formatDate(item.last_visit_date)}
        </Text>
      </View>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{item.total_visits} lần</Text>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Thanh tìm kiếm */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#94a3b8" />
        <TextInput 
          style={styles.searchInput} 
          placeholder="Tìm theo tên hoặc SĐT..." 
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#94a3b8"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color="#94a3b8" />
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        data={filteredPatients}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={['#2f6fed']} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="people-outline" size={64} color="#cbd5e1" />
            <Text style={styles.emptyText}>Chưa có bệnh nhân nào</Text>
            <Text style={styles.emptySubText}>Danh sách bệnh nhân đã từng khám sẽ hiển thị ở đây.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    margin: 16,
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    gap: 8,
  },
  searchInput: { flex: 1, fontSize: 15, color: '#1e293b' },

  listContent: { paddingHorizontal: 16, paddingBottom: 20 },
  
  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#eff6ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: { fontSize: 20, fontWeight: '700', color: '#2f6fed' },
  
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: '600', color: '#1e293b', marginBottom: 4 },
  detail: { fontSize: 13, color: '#64748b', marginTop: 2, flexDirection: 'row', alignItems: 'center', gap: 4 },
  
  badge: {
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
  },
  badgeText: { fontSize: 12, fontWeight: '600', color: '#475569' },

  emptyState: { alignItems: 'center', marginTop: 80, paddingHorizontal: 32 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#64748b', marginTop: 16 },
  emptySubText: { fontSize: 14, color: '#94a3b8', textAlign: 'center', marginTop: 8 },
});