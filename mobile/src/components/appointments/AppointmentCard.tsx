import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Appointment } from '../../types/appointment';

interface Props {
  appointment: Appointment;
  variant: 'patient' | 'doctor';
  onPress?: () => void;
  onAction?: () => void;
}

export function AppointmentCard({ appointment, variant, onPress, onAction }: Props) {
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

  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Text style={styles.name}>
        {variant === 'patient' ? appointment.doctor?.full_name : appointment.patient_name}
      </Text>
      <Text>{new Date(appointment.appointment_datetime).toLocaleString('vi-VN')}</Text>
      <View style={[styles.badge, { backgroundColor: getStatusColor(appointment.status) }]}>
        <Text style={styles.badgeText}>{appointment.status}</Text>
      </View>
      {variant === 'doctor' && onAction && (
        <TouchableOpacity style={styles.actionBtn} onPress={onAction}>
          <Text style={styles.actionText}>Hành động</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', padding: 16, borderRadius: 8, marginBottom: 8, elevation: 2 },
  name: { fontWeight: 'bold', fontSize: 16 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start', marginTop: 4 },
  badgeText: { color: '#fff', fontSize: 12 },
  actionBtn: { marginTop: 8, backgroundColor: '#e0e7ff', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6, alignSelf: 'flex-start' },
  actionText: { color: '#3730a3', fontWeight: '600' },
});