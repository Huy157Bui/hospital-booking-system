import { Tabs, Redirect } from 'expo-router';
import { useAuthStore } from '../../store/useAuthStore';
import { Ionicons } from '@expo/vector-icons';
import { View, ActivityIndicator } from 'react-native';

export default function PatientLayout() {
  const { user, token, role, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (!token || !user) {
    return <Redirect href="/(auth)/login" />;
  }

  if (String(role).toUpperCase() !== 'PATIENT') {
    return <Redirect href="/(doctor)/today" />;
  }

  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen 
        name="home"
        options={{ 
          title: 'Trang chủ', 
          tabBarIcon: ({ color, size }) => <Ionicons name="home" color={color} size={size} /> 
        }} 
      />
      <Tabs.Screen 
        name="appointments"
        options={{ 
          title: 'Lịch hẹn', 
          tabBarIcon: ({ color, size }) => <Ionicons name="calendar" color={color} size={size} /> 
        }} 
      />
      <Tabs.Screen 
        name="chat"
        options={{ 
          title: 'Chat AI', 
          tabBarIcon: ({ color, size }) => <Ionicons name="chatbubble" color={color} size={size} /> 
        }} 
      />
      <Tabs.Screen 
        name="profile"
        options={{ 
          title: 'Cá nhân', 
          tabBarIcon: ({ color, size }) => <Ionicons name="person" color={color} size={size} /> 
        }} 
      />
      <Tabs.Screen name="appointments/[appointmentId]" options={{ href: null }} />
      <Tabs.Screen name="chat/[sessionId]" options={{ href: null }} />
      <Tabs.Screen name="profile/edit" options={{ href: null }} />
      <Tabs.Screen name="profile/change-password" options={{ href: null }} />
      
      <Tabs.Screen name="doctors" options={{ href: null }} />
      <Tabs.Screen name="payments" options={{ href: null }} />
      <Tabs.Screen name="specialties" options={{ href: null }} />
    </Tabs>
  );
}