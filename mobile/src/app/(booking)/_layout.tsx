import { Stack } from 'expo-router';

export default function BookingLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerTitleAlign: 'center',
        headerStyle: { backgroundColor: '#fff' },
        headerShadowVisible: false,
        headerTintColor: '#333',
      }}
    >
      <Stack.Screen 
        name="specialty" 
        options={{ title: 'Bước 1: Chọn chuyên khoa' }} 
      />
      <Stack.Screen 
        name="doctor" 
        options={{ title: 'Bước 2: Chọn bác sĩ' }} 
      />
      <Stack.Screen 
        name="slot" 
        options={{ title: 'Bước 3: Chọn ngày & giờ' }} 
      />
      <Stack.Screen 
        name="confirm" 
        options={{ title: 'Bước 4: Xác nhận' }} 
      />
      <Stack.Screen 
        name="success" 
        options={{ 
          title: 'Đặt lịch thành công',
          headerShown: false
        }} 
      />
    </Stack>
  );
}