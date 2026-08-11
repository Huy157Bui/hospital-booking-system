import { Stack, useRouter, useSegments } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useAuthStore } from '../store/useAuthStore';

export default function RootLayout() {
  const { isAuthenticated, isLoading, checkAutoLogin } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    checkAutoLogin();
  }, []);

  useEffect(() => {
    if (isLoading) return;
    const inAuthGroup = segments[0] === 'auth';

    if (!isAuthenticated && !inAuthGroup) {
      router.replace('/auth/login');
    } else if (isAuthenticated && inAuthGroup) {
      router.replace('/tabs');
    }
  }, [isAuthenticated, isLoading, segments[0]]);

  return (
    <View style={{ flex: 1 }}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="auth" />
        <Stack.Screen name="tabs" />
      </Stack>

      {isLoading && (
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: '#ffffff',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 999,
          }}
        >
          <ActivityIndicator size="large" color="#0066cc" />
        </View>
      )}
    </View>
  );
}