import { Tabs } from 'expo-router';
import { useAuthStore } from '../../store/useAuthStore';
import { Ionicons } from '@expo/vector-icons';
import { View, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Redirect } from 'expo-router';

export default function DoctorLayout() {
  const { role, isLoading } = useAuthStore();
  const insets = useSafeAreaInsets();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (String(role).toUpperCase() !== 'DOCTOR') {
    return <Redirect href="/(patient)/home" />;
  }

  return (
    <Tabs 
      screenOptions={{ 
        headerShown: true,
        headerTitle: '',
        headerShadowVisible: false,
        headerStyle: {
          backgroundColor: '#ffffff',
        },
        
        // Giữ nguyên cấu hình Tab Bar
        tabBarActiveTintColor: '#2f6fed',
        tabBarInactiveTintColor: '#8e8e93',
        tabBarStyle: { 
          height: 60 + insets.bottom,
          paddingBottom: insets.bottom,
          paddingTop: 8,
          borderTopWidth: 1,
          borderTopColor: '#e2e8f0',
          backgroundColor: '#ffffff',
          elevation: 8,
        }
      }}
    >
      <Tabs.Screen 
        name="today" 
        options={{ 
          title: 'Hôm nay', 
          tabBarIcon: ({ color, size }) => <Ionicons name="medical" color={color} size={size} /> 
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
        name="patient" 
        options={{ 
          title: 'Bệnh nhân', 
          tabBarIcon: ({ color, size }) => <Ionicons name="people" color={color} size={size} /> 
        }} 
      />
      <Tabs.Screen 
        name="profile" 
        options={{ 
          title: 'Cá nhân', 
          tabBarIcon: ({ color, size }) => <Ionicons name="person-circle" color={color} size={size} /> 
        }} 
      />

      <Tabs.Screen name="appointments/[appointmentId]" options={{ href: null }} />
      <Tabs.Screen name="patient/[patientId]" options={{ href: null }} />
      <Tabs.Screen name="profile/schedule" options={{ href: null }} />
    </Tabs>
  );
}