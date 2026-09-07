import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { doctorService } from '../../../services/doctorService';
import { appointmentService } from '../../../services/appointmentService';
import { Appointment } from '../../../types/appointment';

export default function DoctorTodayScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { 
    data: allData = [], 
    isLoading, 
    refetch 
  } = useQuery<Appointment[]>({
    queryKey: ['doctor-appointments'],
    queryFn: async () => {
      const data = await doctorService.getMyAppointments();
      console.log("🟡 [DEBUG] Tổng số lịch hẹn nhận được từ API:", Array.isArray(data) ? data.length : 0);
      return Array.isArray(data) ? data : [];
    },
    refetchOnWindowFocus: true, 
  });

  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch])
  );

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
    switch (appointment.status) {
      case 'PENDING':
      case 'CONFIRMED':
        return (
          <TouchableOpacity 
            style={[styles.actionBtn, styles.startBtn]}
            onPress={async () => {
              try {
                await appointmentService.updateStatus(appointment.id, 'EXAMINING');
                refetch();
                router.push(`/(doctor)/appointments/${appointment.id}`);
              } catch (error) {
                Alert.alert('Lỗi', 'Không thể bắt đầu khám. Vui lòng thử lại.');
              }
            }}
          >
            <Text style={styles.startBtnText}>Bắt đầu khám</Text>
          </TouchableOpacity>
        );
      
      case 'CHECKING_IN':
      case 'EXAMINING':
        return (
          <TouchableOpacity
            style={[styles.actionBtn, styles.recordBtn]}
            onPress={() => router.push(`/(doctor)/appointments/${appointment.id}`)}
          >
            <Text style={styles.recordBtnText}>Ghi hồ sơ</Text>
          </TouchableOpacity>
        );
      
      case 'COMPLETED':
      case 'PAID':
        return (
          <View style={styles.completedBadge}>
            <Text style={styles.completedText}>Đã hoàn thành</Text>
          </View>
        );

      case 'CANCELLED':
        return (
          <View style={styles.cancelledBadge}>
            <Text style={styles.cancelledText}>Đã hủy</Text>
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
  container: { flex: 1, padding: 16, backgroundColor: '#f8f9fa' },
  card: { 
    backgroundColor: '#fff', 
    padding: 16, 
    borderRadius: 12, 
    marginBottom: 12, 
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2 
  },
  patientName: { fontWeight: '700', fontSize: 16, marginBottom: 4, color: '#1f2937' },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6, alignSelf: 'flex-start', marginTop: 8 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  
  actionBtn: { marginTop: 12, paddingVertical: 12, paddingHorizontal: 16, borderRadius: 8, alignItems: 'center' },
  startBtn: { backgroundColor: '#2f6fed' },
  startBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  
  recordBtn: { backgroundColor: '#10b981', marginTop: 12 },
  recordBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },

  completedBadge: { marginTop: 12, paddingVertical: 8, alignItems: 'center', backgroundColor: '#d1fae5', borderRadius: 8 },
  completedText: { color: '#065f46', fontWeight: '600', fontSize: 14 },
  
  cancelledBadge: { marginTop: 12, paddingVertical: 8, alignItems: 'center', backgroundColor: '#fee2e2', borderRadius: 8 },
  cancelledText: { color: '#991b1b', fontWeight: '600', fontSize: 14 },
});