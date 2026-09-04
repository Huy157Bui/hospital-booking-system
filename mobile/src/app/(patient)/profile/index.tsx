// src/app/(patient)/profile/index.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../../store/useAuthStore';
// ✅ ĐÃ XÓA: import userService vì không cần thiết cho màn hình này

export default function PatientProfileScreen() {
  const router = useRouter();
  // ✅ SỬA: Lấy trực tiếp hàm logout từ useAuthStore
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      // useAuthStore đã lo hết: gọi API /auth/logout và clear storage
      await logout(); 
      // Chuyển về màn hình login
      router.replace('/(auth)/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Vẫn cố gắng chuyển về login dù API lỗi để user không bị kẹt
      router.replace('/(auth)/login');
    }
  };

  const confirmLogout = () => {
    Alert.alert('Đăng xuất', 'Bạn có chắc chắn muốn đăng xuất?', [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Đăng xuất', style: 'destructive', onPress: handleLogout },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      {/* Thông tin user */}
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.full_name?.charAt(0) || 'U'}</Text>
        </View>
        <Text style={styles.fullName}>{user?.full_name || 'Chưa cập nhật'}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        {user?.phone && <Text style={styles.phone}>{user.phone}</Text>}
      </View>

      {/* Danh sách chức năng */}
      <View style={styles.menu}>
        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/(patient)/profile/edit')}
        >
          <Text style={styles.menuText}>Sửa thông tin</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/(patient)/profile/change-password')}
        >
          <Text style={styles.menuText}>Đổi mật khẩu</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.menuItem}
          onPress={() => router.push('/(patient)/payments')}
        >
          <Text style={styles.menuText}>Lịch sử thanh toán</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Nút đăng xuất */}
      <TouchableOpacity style={styles.logoutButton} onPress={confirmLogout}>
        <Text style={styles.logoutText}>Đăng xuất</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { alignItems: 'center', paddingVertical: 32, backgroundColor: '#fff' },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#2f6fed',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: { fontSize: 32, color: '#fff', fontWeight: 'bold' },
  fullName: { fontSize: 22, fontWeight: '600', color: '#333' },
  email: { fontSize: 14, color: '#666', marginTop: 4 },
  phone: { fontSize: 14, color: '#666', marginTop: 2 },
  menu: {
    backgroundColor: '#fff',
    marginTop: 16,
    borderRadius: 10,
    marginHorizontal: 16,
  },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  menuText: { fontSize: 16, color: '#333' },
  chevron: { fontSize: 24, color: '#aaa' },
  logoutButton: {
    margin: 16,
    backgroundColor: '#ff3b30',
    paddingVertical: 16,
    borderRadius: 10,
    alignItems: 'center',
  },
  logoutText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});