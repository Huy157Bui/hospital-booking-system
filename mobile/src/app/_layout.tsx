// src/app/_layout.tsx
import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../store/useAuthStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
    },
    mutations: { retry: 1 },
  },
});

export default function RootLayout() {
  const { checkAutoLogin, isLoading } = useAuthStore();

  // Chỉ gọi checkAutoLogin 1 lần duy nhất khi app mount
  useEffect(() => {
    checkAutoLogin();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <View style={{ flex: 1 }}>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(patient)" />
          <Stack.Screen name="(doctor)" />
          <Stack.Screen name="(booking)" options={{ headerShown: false }} />
        </Stack>

        {/* Loading overlay phủ kín màn hình trong lúc checkAutoLogin */}
        {isLoading && (
          <View
            style={{
              position: 'absolute',
              top: 0, left: 0, right: 0, bottom: 0,
              justifyContent: 'center',
              alignItems: 'center',
              backgroundColor: '#fff',
              zIndex: 9999,
            }}
          >
            <ActivityIndicator size="large" color="#0066cc" />
          </View>
        )}
      </View>
    </QueryClientProvider>
  );
}