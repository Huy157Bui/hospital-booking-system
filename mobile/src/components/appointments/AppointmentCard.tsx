import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Appointment } from '../../types/appointment';

interface Props {
  appointment: Appointment;
  variant: 'patient' | 'doctor';
  onPress?: () => void;
  onAction?: () => void; 
}

export function AppointmentCard({ appointment, variant, onPress, onAction }: Props) {
  
  const getStatusColor = (status: string | undefined) => {
    switch (status?.toUpperCase()) {
      case 'PENDING': return '#f59e0b';
      case 'CONFIRMED': return '#0284c7';
      case 'CHECKING_IN': return '#8b5cf6';
      case 'EXAMINING': return '#8b5cf6';
      case 'COMPLETED': return '#10b981';
      case 'PAID': return '#10b981';
      case 'CANCELLED': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusLabel = (status: string | undefined) => {
    switch (status?.toUpperCase()) {
      case 'PENDING': return 'Chờ xác nhận';
      case 'CONFIRMED': return 'Đã xác nhận';
      case 'CHECKING_IN': return 'Đang check-in';
      case 'EXAMINING': return 'Đang khám';
      case 'COMPLETED': return 'Hoàn thành';
      case 'PAID': return 'Đã thanh toán';
      case 'CANCELLED': return 'Đã hủy';
      default: return status || 'Không rõ';
    }
  };

  const displayName = variant === 'patient' 
    ? (appointment.slot?.schedule?.doctor?.user?.full_name || 'Đang cập nhật')
    : (appointment.patient?.user?.full_name || appointment.patient_name || 'Bệnh nhân');

  const specialtyName = appointment.slot?.schedule?.doctor?.specialty?.name || 'Chuyên khoa';
  
  const rawDate = appointment.slot?.schedule?.work_date || new Date().toISOString().split('T')[0];
  const rawTime = appointment.slot?.start_time || '08:00:00';

  const isoString = `${rawDate}T${rawTime}`;
  const dateObj = new Date(isoString);
  const isValidDate = !isNaN(dateObj.getTime());

  const displayDate = isValidDate 
    ? dateObj.toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
    : 'Ngày chưa xác định';

  const displayTime = isValidDate && rawTime 
    ? rawTime.substring(0, 5) 
    : 'Giờ chưa xác định';

  const canCancel = variant === 'patient' && (appointment.status === 'PENDING' || appointment.status === 'CONFIRMED');

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.headerRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.name}>{displayName}</Text>
          {specialtyName && <Text style={styles.specialty}>{specialtyName}</Text>}
        </View>
        
        <View style={[styles.badge, { backgroundColor: getStatusColor(appointment.status) }]}>
          <Text style={styles.badgeText}>{getStatusLabel(appointment.status)}</Text>
        </View>
      </View>

      <Text style={styles.datetime}>
        {displayDate} - {displayTime}
      </Text>

      {variant === 'patient' && onAction && (appointment.status === 'PENDING' || appointment.status === 'CONFIRMED') && (
        <TouchableOpacity style={styles.cancelBtn} onPress={onAction} activeOpacity={0.7}>
          <Text style={styles.cancelText}>Hủy lịch hẹn</Text>
        </TouchableOpacity>
      )}

      {variant === 'doctor' && onAction && appointment.status !== 'COMPLETED' && appointment.status !== 'CANCELLED' && (
        <TouchableOpacity style={styles.actionBtn} onPress={onAction}>
          <Text style={styles.actionText}>
            {appointment.status === 'PENDING' ? 'Bắt đầu khám (Check-in)' : 
             appointment.status === 'CHECKING_IN' ? 'Chuyển sang Đang khám' : 
             'Hoàn tất khám'}
          </Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: { 
    backgroundColor: '#fff', 
    padding: 16, 
    borderRadius: 12, 
    marginBottom: 12, 
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  headerRow: { 
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  name: { fontWeight: 'bold', fontSize: 16, color: '#333', marginBottom: 2 },
  specialty: { fontSize: 13, color: '#666', marginBottom: 4 }, 
  datetime: { fontSize: 14, color: '#666', marginBottom: 8 },
  badge: { 
    paddingHorizontal: 10, 
    paddingVertical: 4, 
    borderRadius: 20, 
    alignSelf: 'flex-start', 
  },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '600' }, 
  
  cancelBtn: { 
    marginTop: 8, 
    backgroundColor: '#fee2e2', 
    paddingVertical: 10, 
    borderRadius: 8, 
    alignItems: 'center' 
  },
  cancelText: { color: '#dc2626', fontWeight: '600', fontSize: 14 },

  actionBtn: { 
    marginTop: 12, 
    backgroundColor: '#e0e7ff', 
    paddingVertical: 10, 
    paddingHorizontal: 16, 
    borderRadius: 8, 
    alignSelf: 'flex-start' 
  },
  actionText: { color: '#3730a3', fontWeight: '600', fontSize: 14 },
});