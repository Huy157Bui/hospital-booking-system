import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../../store/useAuthStore';
import { Ionicons } from '@expo/vector-icons';

export default function DoctorProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="person-circle" size={80} color="#2f6fed" />
        <Text style={styles.name}>{user?.full_name || 'Bác sĩ'}</Text>
        <Text style={styles.email}>{user?.email || 'Chưa có email'}</Text>
      </View>

      <View style={styles.menu}>
        <TouchableOpacity 
          style={styles.menuItem} 
          onPress={() => router.push('/(doctor)/profile/schedule')}
        >
          <Ionicons name="time-outline" size={22} color="#2f6fed" />
          <Text style={styles.menuText}>Quản lý lịch làm việc</Text>
          <Ionicons name="chevron-forward" size={20} color="#cbd5e1" style={{ marginLeft: 'auto' }} />
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color="#fff" />
        <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  header: { alignItems: 'center', paddingVertical: 32, backgroundColor: '#fff', borderRadius: 16, marginBottom: 16 },
  name: { fontSize: 20, fontWeight: '700', color: '#1e293b', marginTop: 12 },
  email: { fontSize: 14, color: '#64748b', marginTop: 4 },
  menu: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden' },
  menuItem: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  menuText: { fontSize: 16, color: '#334155', fontWeight: '500', marginLeft: 12 },
  logoutButton: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#ef4444', paddingVertical: 16, borderRadius: 12, marginTop: 32, gap: 8 },
  logoutText: { color: '#fff', fontSize: 16, fontWeight: '700' }
});