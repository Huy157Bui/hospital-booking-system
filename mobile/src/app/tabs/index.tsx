import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuthStore } from '../../store/useAuthStore';

export default function HomeScreen() {
  const { user, logout } = useAuthStore();

  return (
    <View style={styles.container}>
      <Text style={styles.welcome}>Xin chào, {user?.full_name || user?.username}!</Text>
      <Text style={styles.info}>Email: {user?.email}</Text>
      <Text style={styles.info}>Vai trò: {user?.role}</Text>
      <Text style={styles.info}>Số điện thoại: {user?.phone || 'Chưa cập nhật'}</Text>

      <TouchableOpacity style={styles.logoutButton} onPress={logout}>
        <Text style={styles.logoutText}>Đăng xuất</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    backgroundColor: '#fff',
    justifyContent: 'center',
  },
  welcome: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#0066cc',
    marginBottom: 16,
  },
  info: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  logoutButton: {
    marginTop: 32,
    backgroundColor: '#ff4d4f',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});