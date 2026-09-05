import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router'; // ✅ THÊM useFocusEffect
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { doctorService } from '../../../services/doctorService';
import { appointmentService } from '../../../services/appointmentService';
import { Appointment } from '../../../types/appointment';

export default function DoctorTodayScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // ✅ FIX 1: Khai báo rõ kiểu dữ liệu <Appointment[]> để TypeScript không báo 'unknown'
  const { 
    data: allData = [], 
    isLoading, 
    refetch 
  } = useQuery<Appointment[]>({
    queryKey: ['doctor-appointments'],
    queryFn: async () => {
      const data = await doctorService.getMyAppointments();
      console.log("🟡 [DEBUG] Tổng số lịch hẹn nhận được từ API:", Array.isArray(data) ? data.length : 0);
      return Array.isArray(data) ? data : []; // Fallback an toàn
    },
    // ✅ FIX 2: Đổi tên thuộc tính cho đúng chuẩn React Query
    refetchOnWindowFocus: true, 
  });

  // ✅ FIX 3 (QUAN TRỌNG CHO MOBILE): 
  // Tự động gọi refetch() mỗi khi màn hình này được focus (ví dụ: bấm router.back() quay về)
  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch])
  );

  // Logic lọc dữ liệu TÁCH BIỆT, chỉ chạy khi allData thay đổi
  const todayAppointments = React.useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    console.log("🟢 [DEBUG] Ngày hôm nay cần lọc:", today);
    
    const filtered = (allData || []).filter((item: Appointment) => {
      const workDate = item.slot?.schedule?.work_date;
      console.log(`🔍 [DEBUG] Kiểm tra lịch ID ${item.id}: work_date = ${workDate}, status = ${item.status}`);
      return workDate === today && item.status !== 'CANCELLED';
    }).sort((a: Appointment, b: Appointment) => {
      return (a.slot?.start_time || '').localeCompare(b.slot?.start_time || '');
    });
    
    console.log("🟢 [DEBUG] Số lịch hẹn sau khi lọc cho hôm nay:", filtered.length);
    return filtered;
  }, [allData]);

  const onRefresh = () => {
    refetch();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING': return 'Chờ xác nhận';
      case 'CONFIRMED': return 'Đã xác nhận';
      case 'CHECKING_IN': return 'Đang check-in';
      case 'EXAMINING': return 'Đang khám';
      case 'COMPLETED': return 'Hoàn thành';
      case 'PAID': return 'Đã thanh toán';
      case 'CANCELLED': return 'Đã hủy';
      default: return status;
    }
  };

  const getActionButton = (appointment: Appointment) => {
    const handleStatusChange = async (newStatus: string) => {
      Alert.alert(
        'Xác nhận thay đổi',
        `Bạn có chắc muốn chuyển trạng thái sang "${newStatus}" không?`,
        [
          { text: 'Hủy', style: 'cancel' },
          {
            text: 'Đồng ý',
            onPress: async () => {
              try {
                await appointmentService.updateStatus(appointment.id, newStatus as any);
                Alert.alert('Thành công', 'Đã cập nhật trạng thái lịch hẹn.');
                refetch(); // ✅ Dùng refetch() trực tiếp thay vì onRefresh()
              } catch (error) {
                console.error('Lỗi cập nhật trạng thái:', error);
                Alert.alert('Lỗi', 'Không thể cập nhật trạng thái. Vui lòng thử lại.');
              }
            }
          }
        ]
      );
    };

    switch (appointment.status) {
      case 'PENDING':
      case 'CONFIRMED':
        return (
          <TouchableOpacity 
            style={[styles.actionBtn, styles.confirmBtn]}
            onPress={() => handleStatusChange('CHECKING_IN')}
          >
            <Text style={[styles.actionText, styles.confirmText]}>
              {appointment.status === 'PENDING' ? 'Xác nhận & Check-in' : 'Bắt đầu khám (Check-in)'}
            </Text>
          </TouchableOpacity>
        );
      
      case 'CHECKING_IN':
      case 'EXAMINING':
        return (
          <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
            <TouchableOpacity
              style={styles.actionBtn}
              onPress={async () => {
                if (appointment.status === 'CHECKING_IN') {
                  try {
                    await appointmentService.updateStatus(appointment.id, 'EXAMINING');
                    refetch(); // ✅ Refresh ngay sau khi đổi status
                  } catch (error) {
                    Alert.alert('Lỗi', 'Không thể cập nhật trạng thái.');
                    return;
                  }
                }
                router.push(`/(doctor)/appointments/${appointment.id}`);
              }}
            >
              <Text style={styles.actionText}>Ghi hồ sơ</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: '#10b981' }]}
              onPress={() => handleStatusChange('COMPLETED')}
            >
              <Text style={[styles.actionText, { color: '#fff' }]}>Hoàn tất</Text>
            </TouchableOpacity>
          </View>
        );
      
      default:
        return null;
    }
  };

  if (isLoading) {
    return <ActivityIndicator style={{ flex: 1 }} size="large" color="#2f6fed" />;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={todayAppointments}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.patientName}>
              {item.patient?.user?.full_name || item.patient_name || 'Không có tên'}
            </Text>
            <Text>
              Giờ: {item.slot?.start_time ? item.slot.start_time.substring(0, 5) : 'N/A'} 
              {item.slot?.schedule?.work_date ? ` (Ngày: ${item.slot.schedule.work_date})` : ''}
            </Text>
            <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) }]}>
              <Text style={styles.badgeText}>{getStatusText(item.status)}</Text>
            </View>
            {getActionButton(item)}
          </View>
        )}
        ListEmptyComponent={
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 40 }}>
            <Text style={{ color: '#666', fontSize: 16 }}>Không có lịch hẹn nào cho ngày hôm nay.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f5f5f5' },
  card: { backgroundColor: '#fff', padding: 16, borderRadius: 8, marginBottom: 8, elevation: 2 },
  patientName: { fontWeight: 'bold', fontSize: 16, marginBottom: 4 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, alignSelf: 'flex-start', marginTop: 8 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  actionBtn: { marginTop: 12, backgroundColor: '#e0e7ff', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 6, alignSelf: 'flex-start' },
  actionText: { color: '#3730a3', fontWeight: '600' },
  confirmBtn: { backgroundColor: '#10b981' },
  confirmText: { color: '#fff' },
});