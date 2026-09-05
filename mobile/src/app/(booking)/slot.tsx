import React, { useEffect, useState } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, 
  ActivityIndicator, Alert 
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useBookingStore } from '../../store/useBookingStore';
import { scheduleService } from '../../services/scheduleService';
import { ScheduleSlotStatus } from '../../types/schedule';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function BookingSlotScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { doctorId, doctorName, specialtyName, setSlot } = useBookingStore();

  const [schedules, setSchedules] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);

  useEffect(() => {
    if (!doctorId) return;

    const fetchSchedule = async () => {
      try {
        setIsLoading(true);
        const data = await scheduleService.getDoctorSchedule(doctorId);
        const safeData = Array.isArray(data) ? data : [];
        
        setSchedules(safeData);
        
        const firstDate = safeData.length > 0 ? (safeData[0].work_date || safeData[0].date) : null;
        if (firstDate) {
          setSelectedDate(firstDate);
        }
      } catch (error) {
        Alert.alert('Lỗi', 'Không thể tải lịch khám của bác sĩ.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSchedule();
  }, [doctorId]);

  if (!doctorId) {
    return (
      <View style={styles.center}>
        <Ionicons name="alert-circle-outline" size={48} color="#f59e0b" />
        <Text style={styles.emptyText}>Vui lòng chọn bác sĩ trước khi chọn lịch.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryButton}>
          <Text style={styles.retryText}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const currentSchedule = schedules.find((s: any) => (s.work_date || s.date) === selectedDate);
  
  const availableSlots: any[] = (currentSchedule?.slots || []).filter(
    (slot: any) => slot.status === ScheduleSlotStatus.AVAILABLE
  );

  const formatDate = (dateString: string) => {
    if (!dateString) return '...';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' });
    } catch (e) {
      return dateString;
    }
  };

  const formatTime = (timeString: string) => {
    if (!timeString) return '--:--';
    return timeString.substring(0, 5);
  };

  const handleContinue = () => {
    if (!selectedDate || !selectedSlotId) {
      Alert.alert('Thông báo', 'Vui lòng chọn ngày và khung giờ khám.');
      return;
    }
    
    const selectedSlotObj = availableSlots.find((s: any) => s.id === selectedSlotId);
    const timeString = selectedSlotObj ? formatTime(selectedSlotObj.start_time) : '';

    setSlot(selectedDate, selectedSlotId, timeString);
    
    router.push('/(booking)/confirm');
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
        <Text style={styles.loadingText}>Đang tải lịch khám...</Text>
      </View>
    );
  }

  if (schedules.length === 0) {
    return (
      <View style={styles.center}>
        <Ionicons name="calendar-outline" size={48} color="#ccc" />
        <Text style={styles.emptyText}>Bác sĩ hiện chưa có lịch khám nào.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryButton}>
          <Text style={styles.retryText}>Quay lại chọn bác sĩ khác</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Chọn lịch khám</Text>
        <Text style={styles.headerSubtitle}>{doctorName} • {specialtyName}</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text style={styles.sectionTitle}>Chọn ngày khám</Text>
        
        <View>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.dateStrip}
          >
            {schedules.map((schedule: any, index: number) => {
              const workDate = schedule.work_date || schedule.date || '';
              const scheduleId = schedule.id ?? index;
              const isSelected = selectedDate === workDate;

              return (
                <TouchableOpacity
                  key={`date-${String(scheduleId)}`}
                  activeOpacity={0.7}
                  style={[styles.dateCard, isSelected && styles.dateCardSelected]}
                  onPress={() => {
                    setSelectedDate(workDate);
                    setSelectedSlotId(null);
                  }}
                >
                  <Text style={[styles.dateText, isSelected && styles.dateTextSelected]}>
                    {formatDate(workDate)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        <Text style={styles.sectionTitle}>Chọn khung giờ</Text>
        {availableSlots.length === 0 ? (
          <View style={styles.noSlotContainer}>
            <Ionicons name="lock-closed" size={24} color="#856404" style={{ marginBottom: 8 }} />
            <Text style={styles.noSlotText}>Các khung giờ trong ngày này đã được đặt hết.</Text>
            <Text style={[styles.noSlotText, { fontSize: 12, marginTop: 4 }]}>Vui lòng chọn ngày khác.</Text>
          </View>
        ) : (
          <View style={styles.slotGrid}>
            {availableSlots.map((slot: any, index: number) => {
              const slotId = slot.id ?? index;
              const isSelected = selectedSlotId === slotId;

              return (
                <TouchableOpacity
                  key={`slot-${String(slotId)}`}
                  activeOpacity={0.7}
                  style={[styles.slotCard, isSelected && styles.slotCardSelected]}
                  onPress={() => setSelectedSlotId(slotId)}
                >
                  <Text style={[styles.slotText, isSelected && styles.slotTextSelected]}>
                    {formatTime(slot.start_time)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}>
        <TouchableOpacity
          style={[styles.continueButton, (!selectedDate || !selectedSlotId) && styles.continueButtonDisabled]}
          onPress={handleContinue}
          disabled={!selectedDate || !selectedSlotId}
          activeOpacity={0.8}
        >
          <Text style={styles.continueButtonText}>Tiếp tục</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loadingText: { marginTop: 12, color: '#666' },
  emptyText: { marginTop: 12, color: '#888', fontSize: 16, textAlign: 'center' },
  retryButton: { marginTop: 16, paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
  header: { paddingHorizontal: 20, paddingVertical: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  headerTitle: { fontSize: 14, color: '#666', marginBottom: 4 },
  headerSubtitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  scrollContent: { padding: 20, paddingBottom: 120 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 12 },
  dateStrip: { flexDirection: 'row', gap: 12, marginBottom: 24 },
  dateCard: { paddingHorizontal: 16, paddingVertical: 12, backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#e0e0e0', minWidth: 90, alignItems: 'center' },
  dateCardSelected: { backgroundColor: '#2f6fed', borderColor: '#2f6fed', shadowColor: '#2f6fed', shadowOpacity: 0.3, shadowRadius: 4, elevation: 3 },
  dateText: { fontSize: 14, fontWeight: '500', color: '#666' },
  dateTextSelected: { color: '#fff', fontWeight: '600' },
  slotGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  slotCard: { width: '30%', paddingVertical: 12, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#e0e0e0', alignItems: 'center', justifyContent: 'center' },
  slotCardSelected: { backgroundColor: '#2f6fed', borderColor: '#2f6fed', shadowColor: '#2f6fed', shadowOpacity: 0.3, shadowRadius: 4, elevation: 3 },
  slotText: { fontSize: 15, fontWeight: '600', color: '#333' },
  slotTextSelected: { color: '#fff' },
  noSlotContainer: { padding: 20, backgroundColor: '#fff3cd', borderRadius: 8, alignItems: 'center' },
  noSlotText: { color: '#856404', fontWeight: '500' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e0e0e0', shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, elevation: 5 },
  continueButton: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#2f6fed', paddingVertical: 16, borderRadius: 12, gap: 8 },
  continueButtonDisabled: { backgroundColor: '#a0c4ff' },
  continueButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});