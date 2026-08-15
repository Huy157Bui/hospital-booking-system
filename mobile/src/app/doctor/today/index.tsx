import { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { doctorService } from '../../../services/doctorService';
import { Appointment } from '../../../types/appointment';

export default function DoctorTodayScreen() {
  const router = useRouter();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchToday = async () => {
    const today = new Date().toISOString().split('T')[0];
    try {
      const data = await doctorService.getMyAppointments({ date: today });
      setAppointments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchToday();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchToday();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'upcoming': return '#0284c7';
      case 'in_progress': return '#8b5cf6';
      case 'completed': return '#10b981';
      case 'cancelled': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getActionButton = (appointment: Appointment) => {
    switch (appointment.status) {
      case 'upcoming':
        return (
          <TouchableOpacity style={styles.actionBtn}>
            <Text style={styles.actionText}>Bắt đầu khám</Text>
          </TouchableOpacity>
        );
      case 'in_progress':
        return (
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => router.push({ pathname: '/doctor/appointments/[appointmentId]', params: { appointmentId: appointment.id } })}
          >
            <Text style={styles.actionText}>Ghi hồ sơ</Text>
          </TouchableOpacity>
        );
      default:
        return null;
    }
  };

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;

  return (
    <View style={styles.container}>
      <FlatList
        data={appointments}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.patientName}>{item.patient_name || 'Không có tên'}</Text>
            <Text>Giờ: {new Date(item.appointment_datetime).toLocaleTimeString('vi-VN')}</Text>
            <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) }]}>
              <Text style={styles.badgeText}>{item.status}</Text>
            </View>
            {getActionButton(item)}
          </View>
        )}
        ListEmptyComponent={<Text>Không có lịch hẹn hôm nay</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f5f5f5' },
  card: { backgroundColor: '#fff', padding: 16, borderRadius: 8, marginBottom: 8, elevation: 2 },
  patientName: { fontWeight: 'bold', fontSize: 16 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start', marginTop: 4 },
  badgeText: { color: '#fff', fontSize: 12 },
  actionBtn: { marginTop: 8, backgroundColor: '#e0e7ff', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6, alignSelf: 'flex-start' },
  actionText: { color: '#3730a3', fontWeight: '600' },
});