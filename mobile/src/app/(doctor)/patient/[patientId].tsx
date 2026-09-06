import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, ActivityIndicator, ScrollView, 
  TouchableOpacity, Modal 
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';

import { doctorService } from '../../../services/doctorService';
import { PatientSummary } from '../../../types/patient';

export default function PatientDetailScreen() {
  const router = useRouter();
  const { patientId } = useLocalSearchParams<{ patientId: string }>();
  
  const [selectedExam, setSelectedExam] = useState<any | null>(null);

  const { data: patient, isLoading: isLoadingPatient } = useQuery<PatientSummary>({
    queryKey: ['patient-summary', patientId],
    queryFn: async () => {
      const patients = await doctorService.getPatients();
      const found = patients.find((p) => p.id === Number(patientId));
      if (!found) throw new Error('Không tìm thấy bệnh nhân');
      return found;
    },
    enabled: !!patientId,
  });

  const { data: medicalHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['patient-medical-history', patientId],
    queryFn: async () => {
      return await doctorService.getPatientMedicalRecords(Number(patientId));
    },
    enabled: !!patientId,
  });

  if (isLoadingPatient) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (!patient) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Không tìm thấy thông tin bệnh nhân.</Text>
      </View>
    );
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Chưa có';
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  return (
    <>
      <Stack.Screen 
        options={{ 
          title: 'Hồ sơ bệnh nhân',
          headerTitleAlign: 'center',
          headerLeft: () => (
            <TouchableOpacity 
              onPress={() => router.back()} 
              style={{ marginLeft: 8, padding: 4 }}
            >
              <Ionicons name="arrow-back" size={24} color="#2f6fed" />
            </TouchableOpacity>
          ),
        }} 
      />
      
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <View style={styles.avatarLarge}>
            <Text style={styles.avatarTextLarge}>{patient.full_name.charAt(0).toUpperCase()}</Text>
          </View>
          <View style={styles.infoBlock}>
            <Text style={styles.nameLarge}>{patient.full_name}</Text>
            <Text style={styles.detailRow}>
              <Ionicons name="call-outline" size={16} color="#64748b" /> {patient.phone || 'Chưa có SĐT'}
            </Text>
            <Text style={styles.detailRow}>
              <Ionicons name="calendar-outline" size={16} color="#64748b" /> 
              Ngày sinh: {formatDate(patient.date_of_birth)}
            </Text>
            <Text style={styles.detailRow}>
              <Ionicons name="people-outline" size={16} color="#64748b" /> 
              Giới tính: {patient.gender === 'MALE' ? 'Nam' : patient.gender === 'FEMALE' ? 'Nữ' : 'Khác'}
            </Text>
          </View>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{patient.total_visits}</Text>
            <Text style={styles.statLabel}>Lần khám</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{formatDate(patient.last_visit_date)}</Text>
            <Text style={styles.statLabel}>Khám gần nhất</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Lịch sử khám bệnh</Text>
        
        {isLoadingHistory ? (
          <ActivityIndicator size="small" color="#2f6fed" style={{ marginTop: 20 }} />
        ) : !medicalHistory || medicalHistory.examinations.length === 0 ? (
          <View style={styles.emptyHistory}>
            <Ionicons name="document-text-outline" size={48} color="#cbd5e1" />
            <Text style={styles.emptyText}>Chưa có lịch sử khám nào.</Text>
          </View>
        ) : (
          medicalHistory.examinations.map((exam: any, index: number) => (
            <View key={exam.id || index} style={styles.historyCard}>
              <View style={styles.historyHeader}>
                <Text style={styles.historyDate}>{formatDate(exam.examined_at || exam.created_date)}</Text>
                <View style={styles.statusBadge}>
                  <Text style={styles.statusText}>{exam.status || 'Hoàn thành'}</Text>
                </View>
              </View>
              
              {exam.diagnosis && (
                <View style={styles.historyRow}>
                  <Text style={styles.label}>Chuẩn đoán:</Text>
                  <Text style={styles.value}>{exam.diagnosis}</Text>
                </View>
              )}
              
              {exam.symptom && (
                <View style={styles.historyRow}>
                  <Text style={styles.label}>Triệu chứng:</Text>
                  <Text style={styles.value} numberOfLines={2}>{exam.symptom}</Text>
                </View>
              )}

              <TouchableOpacity 
                style={styles.viewDetailBtn}
                onPress={() => setSelectedExam(exam)}
              >
                <Text style={styles.viewDetailText}>Xem chi tiết hồ sơ</Text>
                <Ionicons name="chevron-forward" size={16} color="#2f6fed" />
              </TouchableOpacity>
            </View>
          ))
        )}
      </ScrollView>

      {selectedExam && (
        <Modal visible transparent animationType="slide" onRequestClose={() => setSelectedExam(null)}>
          <View style={styles.detailModalOverlay}>
            <View style={styles.detailModalContent}>
              <View style={styles.detailModalHeader}>
                <Text style={styles.detailModalTitle}>Chi tiết ca khám</Text>
                <TouchableOpacity onPress={() => setSelectedExam(null)}>
                  <Ionicons name="close-circle" size={28} color="#64748b" />
                </TouchableOpacity>
              </View>
              
              <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={styles.detailDate}>
                  📅 Ngày khám: {formatDate(selectedExam.examined_at || selectedExam.created_date)}
                </Text>
                
                <View style={styles.detailSection}>
                  <Text style={styles.detailSectionTitle}>🩺 Chỉ số sinh hiệu</Text>
                  <View style={styles.detailStatRow}>
                    <Text style={styles.detailLabel}>Chiều cao:</Text>
                    <Text style={styles.detailValue}>{selectedExam.height ? `${selectedExam.height} cm` : '--'}</Text>
                  </View>
                  <View style={styles.detailStatRow}>
                    <Text style={styles.detailLabel}>Cân nặng:</Text>
                    <Text style={styles.detailValue}>{selectedExam.weight ? `${selectedExam.weight} kg` : '--'}</Text>
                  </View>
                  <View style={styles.detailStatRow}>
                    <Text style={styles.detailLabel}>Huyết áp:</Text>
                    <Text style={styles.detailValue}>{selectedExam.blood_pressure || '--'}</Text>
                  </View>
                  <View style={styles.detailStatRow}>
                    <Text style={styles.detailLabel}>Nhịp tim:</Text>
                    <Text style={styles.detailValue}>{selectedExam.heart_rate ? `${selectedExam.heart_rate} bpm` : '--'}</Text>
                  </View>
                  <View style={styles.detailStatRow}>
                    <Text style={styles.detailLabel}>Nhiệt độ:</Text>
                    <Text style={styles.detailValue}>{selectedExam.temperature ? `${selectedExam.temperature}°C` : '--'}</Text>
                  </View>
                </View>

                <View style={styles.detailSection}>
                  <Text style={styles.detailSectionTitle}>📋 Lâm sàng & Chẩn đoán</Text>
                  <View style={styles.detailRowFlex}>
                    <Text style={styles.detailLabel}>Triệu chứng:</Text>
                    <Text style={styles.detailValue}>{selectedExam.symptom || '--'}</Text>
                  </View>
                  <View style={styles.detailRowFlex}>
                    <Text style={styles.detailLabel}>Tên bệnh:</Text>
                    <Text style={styles.detailValue}>{selectedExam.disease_name || '--'}</Text>
                  </View>
                  <View style={styles.detailRowFlex}>
                    <Text style={styles.detailLabel}>Chẩn đoán:</Text>
                    <Text style={styles.detailValue}>{selectedExam.diagnosis || '--'}</Text>
                  </View>
                  <View style={styles.detailRowFlex}>
                    <Text style={styles.detailLabel}>Kết luận / Hướng điều trị:</Text>
                    <Text style={styles.detailValue}>{selectedExam.conclusion || '--'}</Text>
                  </View>
                </View>

                {selectedExam.note && (
                  <View style={styles.detailSection}>
                    <Text style={styles.detailSectionTitle}>📝 Ghi chú nội bộ</Text>
                    <Text style={styles.detailValue}>{selectedExam.note}</Text>
                  </View>
                )}

                <View style={{ height: 40 }} />
              </ScrollView>
            </View>
          </View>
        </Modal>
      )}
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  content: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  errorText: { color: '#ef4444', fontSize: 16 },

  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  avatarLarge: {
    width: 64, height: 64, borderRadius: 32, backgroundColor: '#eff6ff',
    justifyContent: 'center', alignItems: 'center', marginRight: 16,
  },
  avatarTextLarge: { fontSize: 28, fontWeight: '700', color: '#2f6fed' },
  infoBlock: { flex: 1 },
  nameLarge: { fontSize: 20, fontWeight: '700', color: '#1e293b', marginBottom: 8 },
  detailRow: { fontSize: 14, color: '#64748b', marginTop: 4, flexDirection: 'row', alignItems: 'center', gap: 8 },

  statsContainer: { flexDirection: 'row', gap: 12, marginBottom: 24 },
  statBox: {
    flex: 1, backgroundColor: '#fff', padding: 16, borderRadius: 12,
    alignItems: 'center', borderWidth: 1, borderColor: '#e2e8f0',
  },
  statValue: { fontSize: 18, fontWeight: '700', color: '#2f6fed', marginBottom: 4 },
  statLabel: { fontSize: 12, color: '#64748b', fontWeight: '500' },

  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1e293b', marginBottom: 12 },

  historyCard: {
    backgroundColor: '#fff', padding: 16, borderRadius: 12,
    marginBottom: 12, borderWidth: 1, borderColor: '#e2e8f0',
  },
  historyHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 12, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: '#f1f5f9',
  },
  historyDate: { fontSize: 14, fontWeight: '600', color: '#475569' },
  statusBadge: { backgroundColor: '#dcfce7', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  statusText: { fontSize: 12, fontWeight: '600', color: '#166534' },

  historyRow: { marginBottom: 8 },
  label: { fontSize: 13, color: '#94a3b8', fontWeight: '500', marginBottom: 2 },
  value: { fontSize: 14, color: '#334155', lineHeight: 20 },

  viewDetailBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#f1f5f9',
  },
  viewDetailText: { fontSize: 14, fontWeight: '600', color: '#2f6fed', marginRight: 4 },

  emptyHistory: { alignItems: 'center', paddingVertical: 32 },
  emptyText: { fontSize: 14, color: '#94a3b8', marginTop: 8 },

  detailModalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end',
  },
  detailModalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 20, maxHeight: '85%',
  },
  detailModalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 16, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: '#f1f5f9',
  },
  detailModalTitle: { fontSize: 18, fontWeight: '700', color: '#1e293b' },
  detailDate: { fontSize: 14, color: '#64748b', marginBottom: 16, fontWeight: '500' },
  
  detailSection: {
    backgroundColor: '#f8fafc', padding: 16, borderRadius: 12, marginBottom: 12,
  },
  detailSectionTitle: { fontSize: 15, fontWeight: '700', color: '#2f6fed', marginBottom: 12 },
  detailStatRow: { 
    flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8,
  },
  detailRowFlex: { marginBottom: 10 },
  detailLabel: { fontSize: 13, color: '#64748b', fontWeight: '600' },
  detailValue: { fontSize: 14, color: '#1e293b', fontWeight: '500', flex: 1, textAlign: 'right' },
});