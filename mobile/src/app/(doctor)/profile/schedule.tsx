import React, { useState, useEffect } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, 
  ActivityIndicator, Alert, Switch 
} from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';

import { doctorService } from '../../../services/doctorService';
import { DoctorSchedule, ScheduleSlot, ScheduleSlotStatus } from '../../../types/schedule';

export default function DoctorScheduleScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [updatingSlotId, setUpdatingSlotId] = useState<number | null>(null);

  const { data: schedules, isLoading, refetch } = useQuery<DoctorSchedule[]>({
    queryKey: ['doctor-schedule'],
    queryFn: () => doctorService.getMySchedule(),
  });

  const getNext7DaysSchedules = () => {
    if (!schedules) return [];
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const next7Days = [];
    for (let i = 0; i < 7; i++) {
      const targetDate = new Date(today);
      targetDate.setDate(today.getDate() + i);
      const dateStr = targetDate.toISOString().split('T')[0];
      
      const daySchedule = schedules.find(s => s.work_date === dateStr) || {
        id: 0,
        doctor_id: 0,
        work_date: dateStr,
        status: 'CLOSED' as const,
        slots: []
      };
      next7Days.push(daySchedule);
    }
    return next7Days;
  };

  const next7Days = getNext7DaysSchedules();

  const handleToggleSlot = async (slot: ScheduleSlot) => {
    if (slot.status === ScheduleSlotStatus.BOOKED) {
      Alert.alert('Không thể thay đổi', 'Khung giờ này đã có bệnh nhân đặt lịch.');
      return;
    }

    const newStatus = slot.status === ScheduleSlotStatus.AVAILABLE 
      ? ScheduleSlotStatus.BLOCKED 
      : ScheduleSlotStatus.AVAILABLE;
      
    setUpdatingSlotId(slot.id);

    const oldData = queryClient.getQueryData<DoctorSchedule[]>(['doctor-schedule']);
    if (oldData) {
      const newData = oldData.map(day => ({
        ...day,
        slots: day.slots.map(s => s.id === slot.id ? { ...s, status: newStatus } : s)
      }));
      queryClient.setQueryData(['doctor-schedule'], newData);
    }

    try {
      await doctorService.updateScheduleSlot(slot.id, newStatus);
    } catch (error) {
      if (oldData) {
        queryClient.setQueryData(['doctor-schedule'], oldData);
      }
      Alert.alert('Lỗi', 'Không thể cập nhật lịch. Vui lòng thử lại.');
    } finally {
      setUpdatingSlotId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const days = ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
    return `${days[date.getDay()]}, ${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  return (
    <>
      <Stack.Screen 
        options={{ 
          title: 'Quản lý lịch làm việc',
          headerTitleAlign: 'center',
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()} style={{ marginLeft: 8, padding: 4 }}>
              <Ionicons name="arrow-back" size={24} color="#2f6fed" />
            </TouchableOpacity>
          ),
        }} 
      />
      
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.dateRangeText}>
          📅 Lịch 7 ngày tới
        </Text>

        {next7Days.map((day, index) => (
          <View key={day.work_date || index} style={styles.dayCard}>
            <View style={styles.dayHeader}>
              <Text style={styles.dayTitle}>{formatDate(day.work_date)}</Text>
              <View style={[
                styles.statusBadge, 
                { backgroundColor: day.status === 'OPEN' ? '#dcfce7' : '#fee2e2' }
              ]}>
                <Text style={[
                  styles.statusText, 
                  { color: day.status === 'OPEN' ? '#166534' : '#991b1b' }
                ]}>
                  {day.status === 'OPEN' ? 'Đang mở lịch' : 'Nghỉ'}
                </Text>
              </View>
            </View>

            {day.slots.length === 0 ? (
              <Text style={styles.emptySlotText}>Chưa có khung giờ nào được mở.</Text>
            ) : (
              day.slots.map((slot) => {
                const isUpdating = updatingSlotId === slot.id;
                const isBooked = slot.status === ScheduleSlotStatus.BOOKED;
                const isAvailable = slot.status === ScheduleSlotStatus.AVAILABLE;

                return (
                  <TouchableOpacity
                    key={slot.id}
                    style={[
                      styles.slotRow,
                      isBooked && styles.slotRowBooked,
                      !isAvailable && !isBooked && styles.slotRowBlocked
                    ]}
                    onPress={() => handleToggleSlot(slot)}
                    disabled={isBooked || isUpdating}
                    activeOpacity={isBooked ? 1 : 0.7}
                  >
                    <View style={styles.slotTime}>
                      <Ionicons 
                        name="time-outline" 
                        size={18} 
                        color={isBooked ? '#2f6fed' : '#64748b'} 
                      />
                      <Text style={[
                        styles.slotTimeText,
                        isBooked && { color: '#2f6fed', fontWeight: '600' }
                      ]}>
                        {slot.start_time.substring(0, 5)} - {slot.end_time.substring(0, 5)}
                      </Text>
                    </View>

                    <View style={styles.slotAction}>
                      {isUpdating ? (
                        <ActivityIndicator size="small" color="#2f6fed" />
                      ) : isBooked ? (
                        <View style={styles.bookedBadge}>
                          <Ionicons name="checkmark-circle" size={16} color="#2f6fed" />
                          <Text style={styles.bookedText}>Đã đặt</Text>
                        </View>
                      ) : (
                        <View style={[
                          styles.toggleIndicator,
                          isAvailable ? styles.toggleAvailable : styles.toggleBlocked
                        ]}>
                          <Text style={styles.toggleText}>
                            {isAvailable ? 'Mở' : 'Tắt'}
                          </Text>
                        </View>
                      )}
                    </View>
                  </TouchableOpacity>
                );
              })
            )}
          </View>
        ))}
        
        <View style={{ height: 40 }} />
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  content: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  
  dateRangeText: { fontSize: 16, fontWeight: '600', color: '#475569', marginBottom: 16 },
  
  dayCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  dayHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  dayTitle: { fontSize: 16, fontWeight: '700', color: '#1e293b' },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  statusText: { fontSize: 12, fontWeight: '600' },
  
  emptySlotText: { fontSize: 14, color: '#94a3b8', fontStyle: 'italic', textAlign: 'center', paddingVertical: 8 },
  
  slotRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f8fafc',
  },
  slotRowBooked: { backgroundColor: '#eff6ff', borderRadius: 8, paddingHorizontal: 8, marginBottom: 4 },
  slotRowBlocked: { opacity: 0.6 },
  
  slotTime: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  slotTimeText: { fontSize: 15, color: '#334155', fontWeight: '500' },
  
  slotAction: { alignItems: 'center', justifyContent: 'center', minWidth: 70 },
  
  bookedBadge: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  bookedText: { fontSize: 13, fontWeight: '600', color: '#2f6fed' },
  
  toggleIndicator: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    minWidth: 60,
    alignItems: 'center',
  },
  toggleAvailable: { backgroundColor: '#dcfce7' },
  toggleBlocked: { backgroundColor: '#f1f5f9' },
  toggleText: { fontSize: 13, fontWeight: '600', color: '#475569' },
});