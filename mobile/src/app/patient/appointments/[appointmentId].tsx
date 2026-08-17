import { useLocalSearchParams, Stack } from 'expo-router';
import { View, Text, StyleSheet } from 'react-native';

export default function AppointmentDetailScreen() {
  const { appointmentId } = useLocalSearchParams<{ appointmentId: string }>();
  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: 'Chi tiết lịch hẹn' }} />
      <Text>Chi tiết lịch hẹn ID: {appointmentId}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});