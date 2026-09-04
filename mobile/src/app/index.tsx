// src/app/index.tsx
import { Redirect, useSegments } from 'expo-router';
import { useAuthStore } from '../store/useAuthStore';
import { View, ActivityIndicator } from 'react-native';

export default function Index() {
  const { isAuthenticated, isLoading, role } = useAuthStore();
  const segments = useSegments();

  // 1. Chờ checkAutoLogin xong (isLoading = false) mới quyết định đi đâu
  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
        <ActivityIndicator size="large" color="#0066cc" />
      </View>
    );
  }

  // 2. Logic Redirect tập trung tại đây (chỉ chạy khi isLoading === false)
  if (!isAuthenticated) {
    return <Redirect href="/(auth)/login" />;
  }

  if (role === 'doctor') {
    return <Redirect href="/(doctor)/today" />;
  }

  return <Redirect href="/(patient)/home" />;
}