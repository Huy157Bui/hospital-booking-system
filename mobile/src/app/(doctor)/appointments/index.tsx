import React, { useState, useMemo } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Modal, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';

import { doctorService } from '../../../services/doctorService';
import { Appointment } from '../../../types/appointment';
import { AppointmentCard } from '../../../components/appointments/AppointmentCard';

const STATUS_OPTIONS = [
  { label: 'Tất cả', value: 'ALL' },
  { label: 'Chờ xác nhận', value: 'PENDING' },
  { label: 'Đã xác nhận', value: 'CONFIRMED' },
  { label: 'Đang khám', value: 'EXAMINING' },
  { label: 'Hoàn thành', value: 'COMPLETED' },
];

export default function DoctorAllAppointmentsScreen() {
  const router = useRouter();
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);

  const { data: allAppointments, isLoading } = useQuery<Appointment[]>({
    queryKey: ['doctor-all-appointments'],
    queryFn: async () => {
      return await doctorService.getMyAppointments(); 
    },
  });

  const filteredAppointments = useMemo(() => {
    if (!allAppointments) return [];

    return allAppointments.filter((appt) => {
      if (selectedStatus !== 'ALL' && appt.status !== selectedStatus) {
        return false;
      }

      if (selectedDate) {
        const targetDateStr = selectedDate.toISOString().split('T')[0];
        const apptDateStr = appt.slot?.schedule?.work_date;
        if (apptDateStr !== targetDateStr) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      const dateA = a.slot?.schedule?.work_date || '';
      const dateB = b.slot?.schedule?.work_date || '';
      if (dateA !== dateB) return dateB.localeCompare(dateA);
      return (a.slot?.start_time || '').localeCompare(b.slot?.start_time || '');
    });
  }, [allAppointments, selectedDate, selectedStatus]);

  const onDateChange = (event: any, selected?: Date) => {
    setShowDatePicker(false);
    if (selected) {
      const normalizedDate = new Date(selected);
      normalizedDate.setHours(0, 0, 0, 0);
      setSelectedDate(normalizedDate);
    }
  };

  const clearFilters = () => {
    setSelectedDate(null);
    setSelectedStatus('ALL');
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.filterContainer}>
        <TouchableOpacity style={styles.filterButton} onPress={() => setShowDatePicker(true)}>
          <Ionicons name="calendar-outline" size={18} color="#2f6fed" />
          <Text style={styles.filterButtonText}>
            {selectedDate ? selectedDate.toLocaleDateString('vi-VN') : 'Chọn ngày'}
          </Text>
          {selectedDate && (
            <TouchableOpacity onPress={(e) => { e.stopPropagation(); setSelectedDate(null); }}>
              <Ionicons name="close-circle" size={18} color="#ef4444" />
            </TouchableOpacity>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.filterButton} onPress={() => setShowStatusModal(true)}>
          <Ionicons name="filter-outline" size={18} color="#2f6fed" />
          <Text style={styles.filterButtonText}>
            {STATUS_OPTIONS.find(opt => opt.value === selectedStatus)?.label}
          </Text>
          <Ionicons name="chevron-down" size={18} color="#2f6fed" />
        </TouchableOpacity>

        {(selectedDate || selectedStatus !== 'ALL') && (
          <TouchableOpacity style={styles.clearButton} onPress={clearFilters}>
            <Text style={styles.clearButtonText}>Xóa lọc</Text>
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        data={filteredAppointments}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => {
          const handlePress = () => {
            if (
              item.status === 'EXAMINING' || 
              item.status === 'CHECKING_IN' || 
              item.status === 'COMPLETED' || 
              item.status === 'PAID'
            ) {
              router.push(`/(doctor)/appointments/${item.id}`);
            } else {
              Alert.alert('Chưa thể thực hiện', `Lịch hẹn đang ở trạng thái "${item.status}". Vui lòng bắt đầu khám từ tab "Hôm nay".`);
            }
          };

          return (
            <AppointmentCard
              appointment={item}
              onPress={handlePress} 
              variant="doctor" 
            />
          );
        }}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="calendar-clear-outline" size={64} color="#cbd5e1" />
            <Text style={styles.emptyText}>Không tìm thấy lịch hẹn nào</Text>
            <Text style={styles.emptySubText}>Hãy thử thay đổi bộ lọc hoặc chọn ngày khác.</Text>
          </View>
        }
      />

      {showDatePicker && (
        <DateTimePicker
          value={selectedDate || new Date()}
          mode="date"
          display="default"
          onChange={onDateChange}
        />
      )}

      <Modal visible={showStatusModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Chọn trạng thái</Text>
            {STATUS_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt.value}
                style={[
                  styles.modalOption,
                  selectedStatus === opt.value && styles.modalOptionActive
                ]}
                onPress={() => {
                  setSelectedStatus(opt.value);
                  setShowStatusModal(false);
                }}
              >
                <Text style={[
                  styles.modalOptionText,
                  selectedStatus === opt.value && styles.modalOptionTextActive
                ]}>
                  {opt.label}
                </Text>
                {selectedStatus === opt.value && <Ionicons name="checkmark" size={20} color="#2f6fed" />}
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={styles.modalCloseBtn} onPress={() => setShowStatusModal(false)}>
              <Text style={styles.modalCloseText}>Đóng</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  
  filterContainer: { flexDirection: 'row', padding: 16, gap: 12, alignItems: 'center', backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e2e8f0' },
  filterButton: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#eff6ff', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, gap: 6, flex: 1, justifyContent: 'center' },
  filterButtonText: { color: '#2f6fed', fontWeight: '600', fontSize: 14 },
  clearButton: { paddingHorizontal: 12, paddingVertical: 8 },
  clearButtonText: { color: '#ef4444', fontWeight: '600', fontSize: 14 },

  listContent: { padding: 16, paddingBottom: 100 },
  emptyState: { alignItems: 'center', marginTop: 60, paddingHorizontal: 32 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#64748b', marginTop: 16 },
  emptySubText: { fontSize: 14, color: '#94a3b8', textAlign: 'center', marginTop: 8 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, paddingBottom: 40 },
  modalTitle: { fontSize: 18, fontWeight: '700', color: '#1e293b', marginBottom: 16, textAlign: 'center' },
  modalOption: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  modalOptionActive: { backgroundColor: '#eff6ff', marginHorizontal: -20, paddingHorizontal: 20 },
  modalOptionText: { fontSize: 16, color: '#334155' },
  modalOptionTextActive: { color: '#2f6fed', fontWeight: '600' },
  modalCloseBtn: { marginTop: 20, backgroundColor: '#f1f5f9', paddingVertical: 14, borderRadius: 12, alignItems: 'center' },
  modalCloseText: { color: '#475569', fontWeight: '600', fontSize: 16 },
});