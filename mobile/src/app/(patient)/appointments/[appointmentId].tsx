import React from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, 
  ActivityIndicator, Alert 
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { appointmentService } from '../../../services/appointmentService';
import { Appointment } from '../../../types/appointment';

export default function AppointmentDetailScreen() {
  const { appointmentId } = useLocalSearchParams<{ appointmentId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  // 1. Lấy chi tiết lịch hẹn theo ID
  const { data: appointment, isLoading, isError } = useQuery<Appointment>({
    queryKey: ['appointmentDetail', appointmentId],
    queryFn: async () => {
      return await appointmentService.getById(Number(appointmentId));
    },
    enabled: !!appointmentId,
  });

  // 2. Các hàm helper định dạng (giống với AppointmentCard để đồng bộ)
  const getStatusConfig = (status: string | undefined) => {
    switch (status?.toUpperCase()) {
      case 'PENDING': return { label: 'Chờ xác nhận', color: '#f59e0b', bg: '#fef3c7' };
      case 'CONFIRMED': return { label: 'Đã xác nhận', color: '#0284c7', bg: '#dbeafe' };
      case 'CHECKING_IN': 
      case 'EXAMINING': return { label: 'Đang khám', color: '#8b5cf6', bg: '#ede9fe' };
      case 'COMPLETED': 
      case 'PAID': return { label: 'Hoàn thành', color: '#10b981', bg: '#d1fae5' };
      case 'CANCELLED': return { label: 'Đã hủy', color: '#ef4444', bg: '#fee2e2' };
      default: return { label: 'Không rõ', color: '#6b7280', bg: '#f3f4f6' };
    }
  };

  const formatDateTime = () => {
    if (!appointment?.slot?.schedule?.work_date || !appointment?.slot?.start_time) {
      return { date: 'Chưa có ngày', time: 'Chưa có giờ' };
    }
    const rawDate = appointment.slot.schedule.work_date;
    const rawTime = appointment.slot.start_time;
    const dateObj = new Date(`${rawDate}T${rawTime}`);
    
    return {
      date: dateObj.toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' }),
      time: `${rawTime.substring(0, 5)} - ${appointment.slot.end_time?.substring(0, 5) || '...'}`
    };
  };

  // 3. Xử lý hủy lịch
  const handleCancel = async () => {
    Alert.alert(
      'Xác nhận hủy lịch',
      'Bạn có chắc chắn muốn hủy lịch hẹn này không? Hành động này không thể hoàn tác.',
      [
        { text: 'Không', style: 'cancel' },
        { 
          text: 'Đồng ý', 
          style: 'destructive',
          onPress: async () => {
            try {
              await appointmentService.cancel(Number(appointmentId));
              Alert.alert('Thành công', 'Đã hủy lịch hẹn.');
              queryClient.invalidateQueries({ queryKey: ['myAppointments'] });
              router.replace('/(patient)/appointments'); 
            } catch (error) {
              Alert.alert('Lỗi', 'Không thể hủy lịch hẹn. Vui lòng thử lại.');
            }
          }
        }
      ]
    );
  };

  // 4. Render các trạng thái Loading / Error
  if (isLoading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
        <Text style={styles.loadingText}>Đang tải thông tin...</Text>
      </SafeAreaView>
    );
  }

  if (isError || !appointment) {
    return (
      <SafeAreaView style={styles.center}>
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text style={styles.errorText}>Không tìm thấy thông tin lịch hẹn.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryButton}>
          <Text style={styles.retryText}>Quay lại</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const statusConfig = getStatusConfig(appointment.status);
  const { date, time } = formatDateTime();
  const doctorName = appointment.slot?.schedule?.doctor?.user?.full_name || 'Đang cập nhật';
  const specialtyName = appointment.slot?.schedule?.doctor?.specialty?.name || 'Chuyên khoa';
  const canCancel = appointment.status === 'PENDING' || appointment.status === 'CONFIRMED';

  // 5. Render giao diện chính
  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <Stack.Screen options={{ title: 'Chi tiết lịch hẹn', headerBackTitle: 'Quay lại' }} />
      
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header thông tin bác sĩ */}
        <View style={styles.card}>
          <View style={styles.doctorHeader}>
            <View style={styles.avatarPlaceholder}>
              <Ionicons name="person" size={32} color="#2f6fed" />
            </View>
            <View style={styles.doctorInfo}>
              <Text style={styles.doctorName}>{doctorName}</Text>
              <Text style={styles.specialtyName}>{specialtyName}</Text>
            </View>
          </View>
        </View>

        {/* Thông tin chi tiết */}
        <View style={styles.card}>
          <View style={styles.detailRow}>
            <Ionicons name="calendar-outline" size={22} color="#2f6fed" />
            <View style={styles.detailTextContainer}>
              <Text style={styles.detailLabel}>Ngày khám</Text>
              <Text style={styles.detailValue}>{date}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailRow}>
            <Ionicons name="time-outline" size={22} color="#2f6fed" />
            <View style={styles.detailTextContainer}>
              <Text style={styles.detailLabel}>Giờ khám</Text>
              <Text style={styles.detailValue}>{time}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailRow}>
            <Ionicons name="information-circle-outline" size={22} color="#2f6fed" />
            <View style={styles.detailTextContainer}>
              <Text style={styles.detailLabel}>Trạng thái</Text>
              <View style={[styles.badge, { backgroundColor: statusConfig.bg }]}>
                <Text style={[styles.badgeText, { color: statusConfig.color }]}>
                  {statusConfig.label}
                </Text>
              </View>
            </View>
          </View>

          {appointment.note && (
            <>
              <View style={styles.divider} />
              <View style={styles.detailRow}>
                <Ionicons name="document-text-outline" size={22} color="#2f6fed" />
                <View style={styles.detailTextContainer}>
                  <Text style={styles.detailLabel}>Ghi chú / Triệu chứng</Text>
                  <Text style={styles.detailValue}>{appointment.note}</Text>
                </View>
              </View>
            </>
          )}
        </View>

        {/* Nút hành động */}
        {canCancel && (
          <TouchableOpacity style={styles.cancelButton} onPress={handleCancel} activeOpacity={0.7}>
            <Ionicons name="close-circle-outline" size={22} color="#fff" />
            <Text style={styles.cancelButtonText}>Hủy lịch hẹn này</Text>
          </TouchableOpacity>
        )}
        
        {/* Khoảng trống cuối để không bị che bởi thanh điều hướng nếu có */}
        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loadingText: { marginTop: 12, color: '#666' },
  errorText: { color: '#c62828', marginBottom: 16, textAlign: 'center', fontSize: 15 },
  retryButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
  
  scrollContent: { padding: 16 },
  
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  
  doctorHeader: { flexDirection: 'row', alignItems: 'center' },
  avatarPlaceholder: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: '#e3f2fd',
    justifyContent: 'center', alignItems: 'center', marginRight: 16
  },
  doctorInfo: { flex: 1 },
  doctorName: { fontSize: 18, fontWeight: '700', color: '#1f2937', marginBottom: 4 },
  specialtyName: { fontSize: 14, color: '#6b7280' },
  
  detailRow: { flexDirection: 'row', alignItems: 'flex-start' },
  detailTextContainer: { marginLeft: 16, flex: 1 },
  detailLabel: { fontSize: 13, color: '#9ca3af', marginBottom: 4, textTransform: 'uppercase', fontWeight: '600' },
  detailValue: { fontSize: 15, color: '#374151', fontWeight: '500', lineHeight: 22 },
  
  divider: { height: 1, backgroundColor: '#f3f4f6', marginVertical: 16 },
  
  badge: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, alignSelf: 'flex-start'
  },
  badgeText: { fontSize: 13, fontWeight: '600' },
  
  cancelButton: {
    flexDirection: 'row', justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#ef4444', paddingVertical: 16, borderRadius: 12, gap: 8,
    shadowColor: '#ef4444', shadowOpacity: 0.3, shadowRadius: 4, elevation: 4,
  },
  cancelButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});