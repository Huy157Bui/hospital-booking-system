import { Tabs, Redirect } from 'expo-router';
import { useAuthStore } from '../../store/useAuthStore';
import { Ionicons } from '@expo/vector-icons';
import { View, ActivityIndicator } from 'react-native';

export default function DoctorLayout() {
  const { role, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  // ✅ SO SÁNH VỚI CHỮ IN HOA 'DOCTOR'
  if (String(role).toUpperCase() !== 'DOCTOR') {
    return <Redirect href="/(patient)/home" />;
  }

  return (
    <Tabs screenOptions={{ headerShown: true }}>
      <Tabs.Screen name="today" options={{ title: 'Hôm nay', tabBarIcon: ({ color, size }) => <Ionicons name="today" color={color} size={size} /> }} />
      <Tabs.Screen name="appointments" options={{ title: 'Lịch hẹn', tabBarIcon: ({ color, size }) => <Ionicons name="calendar" color={color} size={size} /> }} />
    </Tabs>
  );
}