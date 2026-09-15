import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, 
  TextInput, ActivityIndicator, Alert, KeyboardAvoidingView, Platform 
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useBookingStore } from '../../store/useBookingStore';
import { useAuthStore } from '../../store/useAuthStore';
import { appointmentService } from '../../services/appointmentService';
import { useQueryClient } from '@tanstack/react-query';

export default function BookingConfirmScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const { 
    doctorName, specialtyName, date, slotTime, slotId, note, 
    setNote, resetBooking 
  } = useBookingStore();

  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!slotId || !date || !doctorName) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Dữ liệu đặt lịch không đầy đủ.</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryButton}>
          <Text style={styles.retryText}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const handleConfirm = async () => {
    if (!slotId) return;

    setIsSubmitting(true);
    try {
      const newAppointment = await appointmentService.create({
        slot_id: slotId,
        note: note.trim() || undefined,
        reason: note.trim() || undefined,
      });

      queryClient.invalidateQueries({ queryKey: ['myAppointments'] });

      const payload = {
        appointmentId: newAppointment?.id?.toString() || 'N/A',
        doctorName, specialty: specialtyName, date, time: slotTime,
      };

      router.replace({ pathname: '/(booking)/success', params: payload });

      setTimeout(() => {
        resetBooking();
      }, 300);

    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Có lỗi xảy ra khi đặt lịch. Vui lòng thử lại.';
      Alert.alert('Đặt lịch thất bại', errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
          
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Xác nhận đặt lịch</Text>
            <Text style={styles.headerSubtitle}>Vui lòng kiểm tra lại thông tin trước khi xác nhận</Text>
          </View>

          <View style={styles.card}>
            <View style={styles.infoRow}>
              <Ionicons name="person" size={20} color="#2f6fed" />
              <View style={styles.infoTextContainer}>
                <Text style={styles.infoLabel}>Bác sĩ</Text>
                <Text style={styles.infoValue}>{doctorName}</Text>
              </View>
            </View>
            
            <View style={styles.divider} />

            <View style={styles.infoRow}>
              <Ionicons name="medkit" size={20} color="#2f6fed" />
              <View style={styles.infoTextContainer}>
                <Text style={styles.infoLabel}>Chuyên khoa</Text>
                <Text style={styles.infoValue}>{specialtyName}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.infoRow}>
              <Ionicons name="calendar" size={20} color="#2f6fed" />
              <View style={styles.infoTextContainer}>
                <Text style={styles.infoLabel}>Ngày khám</Text>
                <Text style={styles.infoValue}>{date ? new Date(date).toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : '...'}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.infoRow}>
              <Ionicons name="time" size={20} color="#2f6fed" />
              <View style={styles.infoTextContainer}>
                <Text style={styles.infoLabel}>Giờ khám</Text>
                <Text style={styles.infoValue}>{slotTime || '...'}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.infoRow}>
              <Ionicons name="card" size={20} color="#2f6fed" />
              <View style={styles.infoTextContainer}>
                <Text style={styles.infoLabel}>Người đặt</Text>
                <Text style={styles.infoValue}>{user?.full_name || 'Bệnh nhân'}</Text>
              </View>
            </View>
          </View>

          <View style={styles.noteSection}>
            <Text style={styles.noteLabel}>Triệu chứng / Ghi chú (Không bắt buộc)</Text>
            <TextInput
              style={styles.noteInput}
              placeholder="Ví dụ: Đau lưng, chóng mặt, cần khám sáng sớm..."
              placeholderTextColor="#999"
              value={note}
              onChangeText={setNote}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.confirmButton, isSubmitting && styles.confirmButtonDisabled]}
            onPress={handleConfirm}
            disabled={isSubmitting}
            activeOpacity={0.8}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Text style={styles.confirmButtonText}>Xác nhận đặt lịch</Text>
                <Ionicons name="checkmark-circle" size={22} color="#fff" />
              </>
            )}
          </TouchableOpacity>
        </View>

      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  errorText: { color: '#c62828', marginBottom: 12, textAlign: 'center', fontSize: 15 },
  retryButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
  
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { marginBottom: 20 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#333', marginBottom: 4 },
  headerSubtitle: { fontSize: 14, color: '#666' },
  
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
    marginBottom: 24,
  },
  infoRow: { flexDirection: 'row', alignItems: 'center' },
  infoTextContainer: { marginLeft: 12, flex: 1 },
  infoLabel: { fontSize: 12, color: '#888', marginBottom: 2 },
  infoValue: { fontSize: 16, fontWeight: '600', color: '#333' },
  divider: { height: 1, backgroundColor: '#f0f0f0', marginVertical: 16 },
  
  noteSection: { marginBottom: 20 },
  noteLabel: { fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 8 },
  noteInput: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    fontSize: 15,
    color: '#333',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    minHeight: 100,
  },
  
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  confirmButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2f6fed',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  confirmButtonDisabled: { backgroundColor: '#a0c4ff' },
  confirmButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});