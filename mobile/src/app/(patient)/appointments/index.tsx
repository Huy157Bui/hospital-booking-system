import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { appointmentService } from '../../../services/appointmentService';
import { AppointmentCard } from '../../../components/appointments/AppointmentCard';
import { Appointment } from '../../../types/appointment';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type TabType = 'upcoming' | 'history';

export default function PatientAppointmentsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<TabType>('upcoming');

  // 1. Lấy dữ liệu bằng React Query
  const { data: allAppointments, isLoading, isError, refetch } = useQuery<Appointment[]>({
    queryKey: ['myAppointments'],
    queryFn: async () => {
      const response: any = await appointmentService.getMyAppointments();
      const rawData = Array.isArray(response) ? response : response?.data || [];
      console.log("🔍 DỮ LIỆU RAW TỪ API (Appointment):", JSON.stringify(rawData[0], null, 2));
      return rawData;
    },
  });

  // ✅ ĐÃ SỬA BƯỚC 3a: Hàm helper lấy ngày giờ an toàn, khớp với Type mới
  const getAppointmentDate = (appt: Appointment) => {
    // Ưu tiên 1: Nếu backend đã gộp sẵn thành 1 chuỗi (như bạn đã thiết kế trong Type)
    if (appt.appointment_datetime) {
      return new Date(appt.appointment_datetime);
    }
    // Ưu tiên 2: Nếu backend trả về dạng nested (đúng chuẩn model SQLAlchemy bạn gửi)
    if (appt.slot?.schedule?.work_date && appt.slot?.start_time) {
      return new Date(`${appt.slot.schedule.work_date}T${appt.slot.start_time}`);
    }
    // Fallback an toàn: Trả về hiện tại nếu không tìm thấy, tránh crash app
    return new Date();
  };

  // ✅ ĐÃ SỬA BƯỚC 3b: Lọc dữ liệu thông minh bằng useMemo (Ưu tiên Status)
  const filteredAppointments = useMemo(() => {
    if (!allAppointments) return [];
    const now = new Date();

    return allAppointments.filter((a) => {
      const apptDate = getAppointmentDate(a);
      
      // Xác định rõ trạng thái cuối cùng của lịch hẹn
      const isCancelled = a.status === 'CANCELLED';
      const isCompleted = a.status === 'COMPLETED';
      const isActive = !isCancelled && !isCompleted; // PENDING, CONFIRMED, CHECKING_IN, EXAMINING, PAID

      if (activeTab === 'upcoming') {
        // Tab Sắp tới: Hiển thị TẤT CẢ các lịch đang hoạt động (isActive).
        // Chúng ta bỏ điều kiện `apptDate > now` để tránh trường hợp user test ngày quá khứ 
        // hoặc lịch bị trễ vẫn được hiển thị để họ biết mà xử lý, thay vì biến mất vào Lịch sử.
        return isActive;
      } else {
        // Tab Lịch sử: CHỈ hiển thị những lịch đã kết thúc vòng đời (Đã hủy hoặc Đã khám xong).
        // Loại bỏ hoàn toàn điều kiện `apptDate <= now` vì nó đang kéo nhầm lịch PENDING vào đây.
        return isCancelled || isCompleted;
      }
    });
  }, [allAppointments, activeTab]);

  const handlePressAppointment = (appointmentId: string | number) => {
    router.push({
      pathname: '/(patient)/appointments/[appointmentId]',
      params: { appointmentId: String(appointmentId) },
    });
  };

  // ✅ Hàm xử lý hủy lịch
  const handleCancelAppointment = async (appointmentId: number) => {
    Alert.alert(
      'Xác nhận hủy lịch',
      'Bạn có chắc chắn muốn hủy lịch hẹn này không?',
      [
        { text: 'Không', style: 'cancel' },
        { 
          text: 'Đồng ý', 
          onPress: async () => {
            try {
              await appointmentService.cancel(appointmentId);
              Alert.alert('Thành công', 'Đã hủy lịch hẹn.');
              // Làm mới danh sách ngay lập tức
              refetch(); 
            } catch (error) {
              Alert.alert('Lỗi', 'Không thể hủy lịch hẹn. Vui lòng thử lại.');
            }
          }
        }
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Không thể tải lịch hẹn.</Text>
        <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
          <Text style={styles.retryText}>Thử lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={[styles.segmentedControl, { marginTop: insets.top > 0 ? 8 : 16 }]}>
        <TouchableOpacity
          style={[styles.segment, activeTab === 'upcoming' && styles.segmentActive]}
          onPress={() => setActiveTab('upcoming')}
        >
          <Text style={[styles.segmentText, activeTab === 'upcoming' && styles.segmentTextActive]}>
            Sắp tới
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.segment, activeTab === 'history' && styles.segmentActive]}
          onPress={() => setActiveTab('history')}
        >
          <Text style={[styles.segmentText, activeTab === 'history' && styles.segmentTextActive]}>
            Lịch sử
          </Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={filteredAppointments}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <AppointmentCard
            appointment={item}
            onPress={() => handlePressAppointment(item.id)}
            onCancel={() => handleCancelAppointment(item.id)} // ✅ THÊM DÒNG NÀY
            variant="patient"
          />
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>
              {activeTab === 'upcoming' ? 'Không có lịch hẹn sắp tới.' : 'Không có lịch sử khám.'}
            </Text>
          </View>
        }
        contentContainerStyle={{ padding: 16, flexGrow: 1 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#e0e0e0',
    borderRadius: 10,
    margin: 16,
    padding: 4,
  },
  segment: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  segmentActive: {
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: { fontSize: 14, color: '#555' },
  segmentTextActive: { color: '#2f6fed', fontWeight: '600' },
  emptyText: { textAlign: 'center', color: '#888', fontSize: 14 },
  errorText: { color: '#c62828', marginBottom: 12 },
  retryButton: { paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
});