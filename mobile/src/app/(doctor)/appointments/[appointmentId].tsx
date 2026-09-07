import React, { useState, useEffect } from 'react';
import { 
  View, Text, ScrollView, TextInput, TouchableOpacity, 
  StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform,
  Modal, FlatList
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { appointmentService } from '../../../services/appointmentService';
import { doctorService } from '../../../services/doctorService';
import { ExaminationRecord, ExaminationRecordCreate } from '../../../types/appointment';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import apiClient from '../../../services/apiClient';

export default function DoctorExaminationScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  const params = useLocalSearchParams();
  const appointmentIdStr = params.appointmentId as string;
  const id = Number(appointmentIdStr);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<ExaminationRecordCreate>({
    symptom: '', diagnosis: '', conclusion: '', disease_name: '',
    height: undefined, weight: undefined, blood_pressure: '',
    heart_rate: undefined, temperature: undefined, note: '', prescriptions: [],
  });

  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [patientHistory, setPatientHistory] = useState<any[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const [showPrescriptionModal, setShowPrescriptionModal] = useState(false);
  const [showMedicineSelector, setShowMedicineSelector] = useState(false);
  const [medicinesList, setMedicinesList] = useState<any[]>([]);
  const [isLoadingMedicines, setIsLoadingMedicines] = useState(false);
  const [searchMedicine, setSearchMedicine] = useState('');

  const [editingPrescriptionIndex, setEditingPrescriptionIndex] = useState<number | null>(null);
  const [prescriptionForm, setPrescriptionForm] = useState({
    medicine_id: '',
    medicine_name: '',
    dosage: '',
    quantity: '',
    instruction: '',
  });

  const { data: appointment, isLoading, isError } = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => appointmentService.getById(id),
    enabled: !!appointmentIdStr && !isNaN(id),
  });

  const queryClient = useQueryClient();
  const isViewOnly = appointment?.status === 'COMPLETED' || appointment?.status === 'PAID';

  const { data: existingRecord, isLoading: isLoadingRecord } = useQuery<ExaminationRecord>({
    queryKey: ['examination-record', id],
    queryFn: async () => {
      const response = await apiClient.get(`/appointments/${id}/record`);
      return response.data;
    },
    enabled: !!id,
    retry: false,
  });

  useEffect(() => {
    if (isViewOnly && existingRecord) {
      setFormData({
        symptom: existingRecord.symptom || '',
        diagnosis: existingRecord.diagnosis || '',
        conclusion: existingRecord.conclusion || '',
        disease_name: existingRecord.disease_name || '',
        height: existingRecord.height ?? undefined,
        weight: existingRecord.weight ?? undefined,
        blood_pressure: existingRecord.blood_pressure || '',
        heart_rate: existingRecord.heart_rate ?? undefined,
        temperature: existingRecord.temperature ?? undefined,
        note: existingRecord.note || '',
        prescriptions: existingRecord.prescriptions || [],
      });
    } else {
      setFormData({
        symptom: '', diagnosis: '', conclusion: '', disease_name: '',
        height: undefined, weight: undefined, blood_pressure: '',
        heart_rate: undefined, temperature: undefined, note: '', prescriptions: [],
      });
    }
  }, [id, isViewOnly, existingRecord]);

  const updateField = (field: keyof ExaminationRecordCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const loadMedicines = async () => {
    if (medicinesList.length > 0) return;
    setIsLoadingMedicines(true);
    try {
      const response = await apiClient.get('/medicines');
      setMedicinesList(response.data || []);
    } catch (error) {
      console.error('❌ Lỗi tải danh sách thuốc:', error);
      Alert.alert('Lỗi', 'Không thể tải danh sách thuốc. Vui lòng thử lại.');
    } finally {
      setIsLoadingMedicines(false);
    }
  };

  const handleAddPrescription = () => {
    setEditingPrescriptionIndex(null);
    setPrescriptionForm({ medicine_id: '', medicine_name: '', dosage: '', quantity: '', instruction: '' });
    setShowPrescriptionModal(true);
    loadMedicines(); 
  };

  const handleEditPrescription = (index: number) => {
    const prescription = formData.prescriptions?.[index] as any;
    const firstItem = prescription?.items?.[0]; 
    
    if (prescription) {
      setEditingPrescriptionIndex(index);
      setPrescriptionForm({
        medicine_id: firstItem?.medicine_id?.toString() || '',
        medicine_name: firstItem?.medicine_name || 'Thuốc đã chọn',
        dosage: firstItem?.dosage || '',
        quantity: firstItem?.quantity?.toString() || '',
        instruction: firstItem?.instruction || '',
      });
      setShowPrescriptionModal(true);
      loadMedicines();
    }
  };

  const handleSelectMedicine = (medicine: any) => {
    setPrescriptionForm(prev => ({
      ...prev,
      medicine_id: medicine.id.toString(),
      medicine_name: medicine.name || medicine.medicine_name || `Thuốc #${medicine.id}`,
    }));
    setShowMedicineSelector(false);
    setSearchMedicine('');
  };

  const handleSavePrescription = () => {
    if (!prescriptionForm.medicine_id || Number(prescriptionForm.medicine_id) <= 0) {
      return Alert.alert('Cảnh báo', 'Vui lòng chọn một loại thuốc hợp lệ.');
    }
    if (!prescriptionForm.quantity || Number(prescriptionForm.quantity) <= 0) {
      return Alert.alert('Cảnh báo', 'Số lượng phải lớn hơn 0.');
    }

    const newPrescription = {
      prescription_type: 1,
      note: "Đơn thuốc trong ca khám",
      items: [
        {
          medicine_id: Number(prescriptionForm.medicine_id),
          quantity: Number(prescriptionForm.quantity),
          dosage: prescriptionForm.dosage,
          instruction: prescriptionForm.instruction,
        }
      ]
    };

    const updatedPrescriptions = [...(formData.prescriptions || [])];
    
    if (editingPrescriptionIndex !== null) {
      updatedPrescriptions[editingPrescriptionIndex] = newPrescription;
    } else {
      updatedPrescriptions.push(newPrescription);
    }

    updateField('prescriptions', updatedPrescriptions);
    setShowPrescriptionModal(false);
  };

  const handleDeletePrescription = (index: number) => {
    Alert.alert(
      'Xác nhận xóa',
      'Bạn có chắc muốn xóa thuốc này khỏi đơn?',
      [
        { text: 'Hủy', style: 'cancel' },
        {
          text: 'Xóa',
          style: 'destructive',
          onPress: () => {
            const updatedPrescriptions = [...(formData.prescriptions || [])];
            updatedPrescriptions.splice(index, 1);
            updateField('prescriptions', updatedPrescriptions);
          },
        },
      ]
    );
  };

  const showBackendError = (error: any) => {
    const details = error.response?.data?.detail;
    if (Array.isArray(details) && details.length > 0) {
      const firstError = details[0];
      const fieldName = firstError.loc ? firstError.loc[firstError.loc.length - 1] : 'Dữ liệu';
      Alert.alert('Dữ liệu không hợp lệ', `Trường "${fieldName}": ${firstError.msg}`);
    } else {
      Alert.alert('Lỗi', error.response?.data?.message || 'Không thể lưu hồ sơ. Vui lòng thử lại.');
    }
  };

  const fetchPatientHistory = async () => {
    const currentPatientId = appointment?.patient?.id || appointment?.patient_id;
    if (!currentPatientId) {
      Alert.alert('Lỗi', 'Không xác định được ID bệnh nhân.');
      return;
    }
    
    setIsLoadingHistory(true);
    setShowHistoryModal(true);
    
    try {
      const data = await doctorService.getPatientMedicalRecords(currentPatientId);
      const allExaminations = data?.examinations || [];
      const pastExaminations = allExaminations.filter((ex: any) => ex.appointment_id !== id);
      setPatientHistory(pastExaminations);
    } catch (error: any) {
      console.error('❌ Lỗi tải lịch sử:', error.response?.data || error.message);
      if (error.response?.status === 403) {
        Alert.alert('Không có quyền', 'Bạn không có quyền xem hồ sơ của bệnh nhân này.');
      } else if (error.response?.status === 404) {
        setPatientHistory([]);
      } else {
        Alert.alert('Lỗi', 'Không thể tải lịch sử khám bệnh. Vui lòng thử lại.');
      }
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSaveRecord = async () => {
    if (!formData.symptom && !formData.diagnosis) {
      return Alert.alert('Cảnh báo', 'Vui lòng nhập ít nhất Triệu chứng hoặc Chẩn đoán.');
    }
    
    const temp = formData.temperature ? Number(formData.temperature) : undefined;
    if (temp !== undefined && (temp < 30 || temp > 45)) {
      return Alert.alert('Sai dữ liệu', 'Nhiệt độ cơ thể phải nằm trong khoảng 30°C - 45°C.');
    }

    const hr = formData.heart_rate ? Number(formData.heart_rate) : undefined;
    if (hr !== undefined && (hr < 30 || hr > 250)) {
      return Alert.alert('Sai dữ liệu', 'Nhịp tim phải nằm trong khoảng 30 - 250 lần/phút.');
    }

    setIsSubmitting(true);
    try {
      const payload = {
        ...formData,
        height: formData.height ? Number(formData.height) : undefined,
        weight: formData.weight ? Number(formData.weight) : undefined,
        heart_rate: hr,
        temperature: temp,
        examined_at: new Date().toISOString(),
      };

      await appointmentService.createExaminationRecord(id, payload);
      
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['doctor-all-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointment', id] });
      queryClient.invalidateQueries({ queryKey: ['examination-record', id] });

      Alert.alert('Thành công', 'Đã lưu hồ sơ và hoàn tất ca khám!', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (error: any) {
      console.error('❌ Lỗi lưu hồ sơ:', error.response?.data || error.message);
      showBackendError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!appointmentIdStr || isNaN(id)) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.errorText}>⚠️ Không tìm thấy ID lịch hẹn.</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (isLoading || isLoadingRecord) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#2f6fed" />
      </View>
    );
  }

  if (isError || !appointment) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.errorText}>Không thể tải thông tin bệnh nhân.</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const patientName = appointment?.patient?.user?.full_name || appointment?.patient_name || 'Bệnh nhân';

  const filteredMedicines = medicinesList.filter((med) => 
    (med.name || med.medicine_name || '').toLowerCase().includes(searchMedicine.toLowerCase()) ||
    med.id.toString().includes(searchMedicine)
  );

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <Stack.Screen 
        options={{ 
          title: 'Hồ sơ khám', 
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
      <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={{ paddingBottom: 100 }} keyboardShouldPersistTaps="handled">
        
        <View style={styles.headerCard}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <View style={{ flex: 1 }}>
              <Text style={styles.headerTitle}>Hồ sơ khám bệnh</Text>
              <Text style={styles.patientName}>{patientName}</Text>
              <Text style={styles.appointmentInfo}>Lý do khám: {appointment?.reason || 'Không có'}</Text>
            </View>
            
            <TouchableOpacity 
              style={styles.historyButton}
              onPress={fetchPatientHistory}
            >
              <Ionicons name="time-outline" size={20} color="#2f6fed" />
              <Text style={styles.historyButtonText}>Lịch sử</Text>
            </TouchableOpacity>
          </View>

          {isViewOnly && (
            <View style={styles.viewOnlyBadge}>
              <Text style={styles.viewOnlyText}>🔒 Chỉ xem - Ca khám đã hoàn thành</Text>
            </View>
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🩺 Chỉ số sinh hiệu</Text>
          <View style={styles.row}>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Chiều cao (cm)</Text>
              <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} keyboardType="numeric" placeholder="VD: 170" value={formData.height?.toString()} onChangeText={(val) => updateField('height', val)} editable={!isViewOnly} />
            </View>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Cân nặng (kg)</Text>
              <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} keyboardType="numeric" placeholder="VD: 65" value={formData.weight?.toString()} onChangeText={(val) => updateField('weight', val)} editable={!isViewOnly} />
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Huyết áp (mmHg)</Text>
              <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} placeholder="VD: 120/80" value={formData.blood_pressure} onChangeText={(val) => updateField('blood_pressure', val)} editable={!isViewOnly} />
            </View>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Nhịp tim (lần/phút)</Text>
              <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} keyboardType="numeric" placeholder="VD: 75" value={formData.heart_rate?.toString()} onChangeText={(val) => updateField('heart_rate', val)} editable={!isViewOnly} />
            </View>
          </View>
          <View style={styles.fullInput}>
            <Text style={styles.label}>Nhiệt độ (°C) - Từ 30 đến 45</Text>
            <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} keyboardType="numeric" placeholder="VD: 37.5" value={formData.temperature?.toString()} onChangeText={(val) => updateField('temperature', val)} editable={!isViewOnly} />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Chẩn đoán</Text>
          <Text style={styles.label}>Triệu chứng chính</Text>
          <TextInput style={[styles.input, styles.textArea, isViewOnly && styles.inputDisabled]} multiline numberOfLines={3} placeholder="Bệnh nhân than phiền..." value={formData.symptom} onChangeText={(val) => updateField('symptom', val)} editable={!isViewOnly} />
          <Text style={styles.label}>Tên bệnh / Chẩn đoán</Text>
          <TextInput style={[styles.input, isViewOnly && styles.inputDisabled]} placeholder="VD: Viêm họng cấp" value={formData.disease_name} onChangeText={(val) => updateField('disease_name', val)} editable={!isViewOnly} />
          <Text style={styles.label}>Kết luận / Hướng điều trị</Text>
          <TextInput style={[styles.input, styles.textArea, isViewOnly && styles.inputDisabled]} multiline numberOfLines={3} placeholder="Nghỉ ngơi, uống nhiều nước..." value={formData.conclusion} onChangeText={(val) => updateField('conclusion', val)} editable={!isViewOnly} />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📝 Ghi chú</Text>
          <TextInput style={[styles.input, styles.textArea, isViewOnly && styles.inputDisabled]} multiline numberOfLines={3} placeholder="Ghi chú dành cho bác sĩ..." value={formData.note} onChangeText={(val) => updateField('note', val)} editable={!isViewOnly} />
        </View>

        <View style={styles.section}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <Text style={styles.sectionTitle}>💊 Đơn thuốc</Text>
            {!isViewOnly && (
              <TouchableOpacity style={styles.addPrescriptionBtn} onPress={handleAddPrescription}>
                <Ionicons name="add-circle" size={20} color="#2f6fed" />
                <Text style={styles.addPrescriptionText}>Thêm thuốc</Text>
              </TouchableOpacity>
            )}
          </View>

          {!formData.prescriptions || formData.prescriptions.length === 0 ? (
            <View style={styles.emptyPrescription}>
              <Ionicons name="leaf-outline" size={32} color="#cbd5e1" />
              <Text style={styles.emptyPrescriptionText}>Chưa có thuốc nào được kê</Text>
            </View>
          ) : (
            formData.prescriptions.map((prescription: any, index: number) => {
              const item = prescription.items?.[0];
              const medName = medicinesList.find(m => m.id === item?.medicine_id)?.name || medicinesList.find(m => m.id === item?.medicine_id)?.medicine_name || `Mã #${item?.medicine_id}`;
              
              return (
                <View key={index} style={styles.prescriptionCard}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.prescriptionName}>💊 {medName}</Text>
                      <Text style={styles.prescriptionDetail}>
                        <Ionicons name="flask-outline" size={14} color="#64748b" /> Liều lượng: {item?.dosage || 'Không rõ'}
                      </Text>
                      <Text style={styles.prescriptionDetail}>
                        <Ionicons name="cube-outline" size={14} color="#64748b" /> Số lượng: {item?.quantity}
                      </Text>
                      {item?.instruction && (
                        <Text style={styles.prescriptionDetail}>
                          <Ionicons name="information-circle-outline" size={14} color="#64748b" /> {item.instruction}
                        </Text>
                      )}
                    </View>
                    {!isViewOnly && (
                      <View style={{ flexDirection: 'row', gap: 8 }}>
                        <TouchableOpacity onPress={() => handleEditPrescription(index)}>
                          <Ionicons name="create-outline" size={20} color="#2f6fed" />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => handleDeletePrescription(index)}>
                          <Ionicons name="trash-outline" size={20} color="#ef4444" />
                        </TouchableOpacity>
                      </View>
                    )}
                  </View>
                </View>
              );
            })
          )}
        </View>

        <View style={styles.buttonContainer}>
          {!isViewOnly && (
            <TouchableOpacity 
              style={[styles.saveButton, isSubmitting && styles.saveButtonDisabled]} 
              onPress={handleSaveRecord} 
              disabled={isSubmitting}
            >
              {isSubmitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveButtonText}>Lưu hồ sơ</Text>}
            </TouchableOpacity>
          )}
        </View>

      </ScrollView>

      {/* MODAL LỊCH SỬ KHÁM (GIỮ NGUYÊN) */}
      <Modal visible={showHistoryModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.historyModalContent}>
            <View style={styles.historyHeader}>
              <Text style={styles.historyTitle}>📜 Lịch sử khám bệnh</Text>
              <TouchableOpacity onPress={() => setShowHistoryModal(false)}>
                <Ionicons name="close-circle" size={28} color="#64748b" />
              </TouchableOpacity>
            </View>

            {isLoadingHistory ? (
              <ActivityIndicator size="large" color="#2f6fed" style={{ marginVertical: 40 }} />
            ) : patientHistory.length === 0 ? (
              <View style={styles.emptyHistory}>
                <Ionicons name="leaf-outline" size={64} color="#10b981" />
                <Text style={styles.emptyHistoryText}>🌱 Khám lần đầu</Text>
                <Text style={styles.emptyHistorySubText}>
                  Bệnh nhân chưa có tiền sử khám bệnh tại hệ thống.
                </Text>
              </View>
            ) : (
              <FlatList
                data={patientHistory}
                keyExtractor={(item) => item.id.toString()}
                renderItem={({ item }) => (
                  <View style={styles.historyItem}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text style={styles.historyDate}>
                        {new Date(item.examined_at || item.created_date).toLocaleDateString('vi-VN')}
                      </Text>
                      <View style={styles.historyBadge}>
                        <Text style={styles.historyBadgeText}>Lần khám cũ</Text>
                      </View>
                    </View>
                    <Text style={styles.historyDiagnosis}>
                      🩺 {item.diagnosis || item.disease_name || 'Chưa có chẩn đoán'}
                    </Text>
                    {item.symptom && (
                      <Text style={styles.historySymptom} numberOfLines={2}>
                        💬 Triệu chứng: {item.symptom}
                      </Text>
                    )}
                    {item.note && (
                      <Text style={styles.historyNote} numberOfLines={2}>
                        📝 Ghi chú: {item.note}
                      </Text>
                    )}
                  </View>
                )}
                contentContainerStyle={{ paddingBottom: 20 }}
              />
            )}
          </View>
        </View>
      </Modal>

      {/* MODAL THÊM/SỬA ĐƠN THUỐC (ĐÃ CẬP NHẬT) */}
      <Modal visible={showPrescriptionModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.prescriptionModalContent}>
            <View style={styles.historyHeader}>
              <Text style={styles.historyTitle}>
                {editingPrescriptionIndex !== null ? 'Sửa thuốc' : 'Thêm thuốc mới'}
              </Text>
              <TouchableOpacity onPress={() => setShowPrescriptionModal(false)}>
                <Ionicons name="close-circle" size={28} color="#64748b" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              {/* ✅ THAY ĐỔI: Nút chọn thuốc thay vì nhập ID */}
              <Text style={styles.label}>Tên thuốc *</Text>
              <TouchableOpacity 
                style={[styles.input, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]} 
                onPress={() => setShowMedicineSelector(true)}
              >
                <Text style={{ color: prescriptionForm.medicine_name ? '#111' : '#999', flex: 1 }}>
                  {prescriptionForm.medicine_name || '🔍 Chọn tên thuốc...'}
                </Text>
                <Ionicons name="chevron-down" size={20} color="#64748b" />
              </TouchableOpacity>
              {/* Hiển thị ID ẩn để debug nếu cần */}
              {prescriptionForm.medicine_id && (
                <Text style={{ fontSize: 11, color: '#94a3b8', marginTop: 4, marginLeft: 4 }}>
                  Mã thuốc hệ thống: {prescriptionForm.medicine_id}
                </Text>
              )}

              <Text style={styles.label}>Liều lượng</Text>
              <TextInput
                style={styles.input}
                placeholder="VD: 1 viên x 3 lần/ngày"
                value={prescriptionForm.dosage}
                onChangeText={(val) => setPrescriptionForm((prev: any) => ({ ...prev, dosage: val }))}
              />

              <Text style={styles.label}>Số lượng *</Text>
              <TextInput
                style={styles.input}
                placeholder="VD: 30"
                keyboardType="numeric"
                value={prescriptionForm.quantity}
                onChangeText={(val) => setPrescriptionForm((prev: any) => ({ ...prev, quantity: val }))}
              />

              <Text style={styles.label}>Hướng dẫn sử dụng</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="VD: Uống sau khi ăn"
                multiline
                numberOfLines={3}
                value={prescriptionForm.instruction}
                onChangeText={(val) => setPrescriptionForm((prev: any) => ({ ...prev, instruction: val }))}
              />

              <TouchableOpacity style={styles.savePrescriptionBtn} onPress={handleSavePrescription}>
                <Text style={styles.savePrescriptionText}>
                  {editingPrescriptionIndex !== null ? 'Cập nhật' : 'Thêm vào đơn'}
                </Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* ✅ MODAL MỚI: CHỌN THUỐC TỪ DANH SÁCH */}
      <Modal visible={showMedicineSelector} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.prescriptionModalContent, { maxHeight: '70%' }]}>
            <View style={styles.historyHeader}>
              <Text style={styles.historyTitle}>Chọn thuốc</Text>
              <TouchableOpacity onPress={() => { setShowMedicineSelector(false); setSearchMedicine(''); }}>
                <Ionicons name="close-circle" size={28} color="#64748b" />
              </TouchableOpacity>
            </View>

            <TextInput
              style={[styles.input, { marginBottom: 12 }]}
              placeholder="🔍 Tìm kiếm tên thuốc hoặc mã..."
              value={searchMedicine}
              onChangeText={setSearchMedicine}
              autoFocus
            />

            {isLoadingMedicines ? (
              <ActivityIndicator size="large" color="#2f6fed" style={{ marginVertical: 20 }} />
            ) : (
              <FlatList
                data={filteredMedicines}
                keyExtractor={(item) => item.id.toString()}
                renderItem={({ item }) => (
                  <TouchableOpacity 
                    style={styles.medicineItem}
                    onPress={() => handleSelectMedicine(item)}
                  >
                    <Text style={styles.medicineName}>{item.name || item.medicine_name || `Thuốc #${item.id}`}</Text>
                    <Text style={styles.medicinePrice}>Mã: {item.id} | {item.price ? `${item.price.toLocaleString()}đ` : 'Liên hệ'}</Text>
                  </TouchableOpacity>
                )}
                ListEmptyComponent={
                  <View style={{ padding: 20, alignItems: 'center' }}>
                    <Text style={{ color: '#64748b' }}>Không tìm thấy thuốc phù hợp.</Text>
                  </View>
                }
              />
            )}
          </View>
        </View>
      </Modal>

    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  errorText: { fontSize: 18, fontWeight: 'bold', color: '#dc2626', marginBottom: 8, textAlign: 'center' },
  backButton: { backgroundColor: '#2f6fed', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 8, marginTop: 16 },
  backButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  headerCard: { backgroundColor: '#fff', padding: 16, margin: 16, borderRadius: 12, borderLeftWidth: 4, borderLeftColor: '#2f6fed' },
  headerTitle: { fontSize: 14, color: '#666', marginBottom: 4 },
  patientName: { fontSize: 20, fontWeight: 'bold', color: '#111', marginBottom: 8 },
  appointmentInfo: { fontSize: 14, color: '#444' },
  viewOnlyBadge: { marginTop: 8, backgroundColor: '#fee2e2', paddingVertical: 6, paddingHorizontal: 12, borderRadius: 8, alignSelf: 'flex-start' },
  viewOnlyText: { color: '#dc2626', fontSize: 13, fontWeight: '600' },
  section: { backgroundColor: '#fff', padding: 16, marginHorizontal: 16, marginBottom: 16, borderRadius: 12 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#2f6fed', marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  halfInput: { width: '48%' },
  fullInput: { width: '100%' },
  label: { fontSize: 13, color: '#555', marginBottom: 6, fontWeight: '500' },
  input: { backgroundColor: '#f9f9f9', borderWidth: 1, borderColor: '#e0e0e0', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, color: '#111' },
  inputDisabled: { backgroundColor: '#f1f5f9', color: '#475569' },
  textArea: { textAlignVertical: 'top', minHeight: 80 },
  buttonContainer: { paddingHorizontal: 16, paddingBottom: 32 },
  saveButton: { backgroundColor: '#2f6fed', paddingVertical: 16, borderRadius: 12, alignItems: 'center' },
  saveButtonDisabled: { backgroundColor: '#93b4f5' },
  saveButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  historyButton: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#eff6ff', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, gap: 6 },
  historyButtonText: { color: '#2f6fed', fontWeight: '600', fontSize: 13 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  historyModalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, maxHeight: '80%' },
  historyHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottomWidth: 1, borderBottomColor: '#f1f5f9', paddingBottom: 12 },
  historyTitle: { fontSize: 18, fontWeight: '700', color: '#1e293b' },
  emptyHistory: { alignItems: 'center', paddingVertical: 40 },
  emptyHistoryText: { fontSize: 20, fontWeight: '700', color: '#10b981', marginTop: 16 },
  emptyHistorySubText: { fontSize: 14, color: '#64748b', marginTop: 8, textAlign: 'center', paddingHorizontal: 20 },
  historyItem: { backgroundColor: '#f8fafc', padding: 16, borderRadius: 12, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#2f6fed' },
  historyDate: { fontSize: 13, color: '#64748b', fontWeight: '600' },
  historyBadge: { backgroundColor: '#dbeafe', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  historyBadgeText: { color: '#2f6fed', fontSize: 11, fontWeight: '600' },
  historyDiagnosis: { fontSize: 15, fontWeight: '700', color: '#0f172a', marginTop: 8 },
  historySymptom: { fontSize: 14, color: '#475569', marginTop: 4 },
  historyNote: { fontSize: 13, color: '#64748b', fontStyle: 'italic', marginTop: 4 },
  addPrescriptionBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#eff6ff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, gap: 4 },
  addPrescriptionText: { color: '#2f6fed', fontWeight: '600', fontSize: 13 },
  emptyPrescription: { alignItems: 'center', paddingVertical: 24 },
  emptyPrescriptionText: { fontSize: 14, color: '#94a3b8', marginTop: 8 },
  prescriptionCard: { backgroundColor: '#f8fafc', padding: 12, borderRadius: 8, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#2f6fed' },
  prescriptionName: { fontSize: 15, fontWeight: '700', color: '#1e293b', marginBottom: 4 },
  prescriptionDetail: { fontSize: 13, color: '#64748b', marginTop: 2, flexDirection: 'row', alignItems: 'center', gap: 4 },
  prescriptionModalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, maxHeight: '85%' },
  savePrescriptionBtn: { backgroundColor: '#2f6fed', paddingVertical: 14, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  savePrescriptionText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  
  medicineItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  medicineName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  medicinePrice: {
    fontSize: 13,
    color: '#64748b',
  }
});