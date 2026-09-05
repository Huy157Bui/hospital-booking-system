import React, { useState, useEffect } from 'react';
import { 
  View, Text, ScrollView, TextInput, TouchableOpacity, 
  StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform 
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { appointmentService } from '../../../services/appointmentService';
import { ExaminationRecordCreate } from '../../../types/appointment';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function DoctorExaminationScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  // 1. Lấy params và parse ID
  const params = useLocalSearchParams();
  const appointmentIdStr = params.appointmentId as string;
  const id = Number(appointmentIdStr);

  // ✅ QUAN TRỌNG: ĐẶT TẤT CẢ HOOKS LÊN ĐẦU (Tránh lỗi Rendered more hooks)
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<ExaminationRecordCreate>({
    symptom: '', diagnosis: '', conclusion: '', disease_name: '',
    height: undefined, weight: undefined, blood_pressure: '',
    heart_rate: undefined, temperature: undefined, note: '', prescriptions: [],
  });

  // Dùng `enabled` để chỉ gọi API khi ID hợp lệ (Thay vì dùng if/return sớm)
  const { data: appointment, isLoading, isError } = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => appointmentService.getById(id),
    enabled: !!appointmentIdStr && !isNaN(id),
  });

  // ✅ FIX 1: Khởi tạo queryClient để invalidate cache sau khi lưu
  const queryClient = useQueryClient();

  // ✅ FIX 2: Reset form về trạng thái rỗng mỗi khi chuyển sang bệnh nhân (id) mới
  // Điều này ngăn chặn hoàn toàn việc dữ liệu bệnh nhân A bị dính sang bệnh nhân B
  useEffect(() => {
    setFormData({
      symptom: '', diagnosis: '', conclusion: '', disease_name: '',
      height: undefined, weight: undefined, blood_pressure: '',
      heart_rate: undefined, temperature: undefined, note: '', prescriptions: [],
    });
  }, [id]); // Chỉ chạy khi id thay đổi

  // Helper update state
  const updateField = (field: keyof ExaminationRecordCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Hàm hiển thị lỗi chi tiết từ Backend
  const showBackendError = (error: any) => {
    const details = error.response?.data?.detail;
    if (Array.isArray(details) && details.length > 0) {
      const firstError = details[0];
      const fieldName = firstError.loc ? firstError.loc[firstError.loc.length - 1] : 'Dữ liệu';
      Alert.alert('Dữ liệu không hợp lệ', `Trường "${fieldName}": ${firstError.msg}`);
    } else {
      Alert.alert('Lỗi', 'Không thể lưu hồ sơ. Vui lòng thử lại.');
    }
  };

  // Xử lý lưu hồ sơ (Có thêm Validation Frontend)
  const handleSaveRecord = async () => {
    if (!formData.symptom && !formData.diagnosis) {
      return Alert.alert('Cảnh báo', 'Vui lòng nhập ít nhất Triệu chứng hoặc Chẩn đoán.');
    }
    
    // Validate Nhiệt độ (30 - 45 độ)
    const temp = formData.temperature ? Number(formData.temperature) : undefined;
    if (temp !== undefined && (temp < 30 || temp > 45)) {
      return Alert.alert('Sai dữ liệu', 'Nhiệt độ cơ thể phải nằm trong khoảng 30°C - 45°C.');
    }

    // Validate Nhịp tim (30 - 250)
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
      
      // ✅ FIX 3: Báo cho React Query biết dữ liệu đã thay đổi
      // Màn hình "Hôm nay" sẽ tự động refetch và ẩn nút "Ghi hồ sơ" do status đã thành COMPLETED
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointment', id] });

      Alert.alert('Thành công', 'Đã lưu hồ sơ khám bệnh!', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (error: any) {
      console.error('❌ Lỗi lưu hồ sơ:', error.response?.data || error.message);
      showBackendError(error); // Hiển thị lỗi chi tiết
    } finally {
      setIsSubmitting(false);
    }
  };

  // ✅ Bây giờ mới đến các khối Return (Sau khi đã khai báo hết Hooks)
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

  if (isLoading) {
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

  const patientName = appointment?.patient?.user?.full_name || 'Bệnh nhân';

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={{ paddingBottom: 100 }} keyboardShouldPersistTaps="handled">
        
        <View style={styles.headerCard}>
          <Text style={styles.headerTitle}>Hồ sơ khám bệnh</Text>
          <Text style={styles.patientName}>{patientName}</Text>
          <Text style={styles.appointmentInfo}>Lý do khám: {appointment?.reason || 'Không có'}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🩺 Chỉ số sinh hiệu</Text>
          <View style={styles.row}>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Chiều cao (cm)</Text>
              <TextInput style={styles.input} keyboardType="numeric" placeholder="VD: 170" value={formData.height?.toString()} onChangeText={(val) => updateField('height', val)} />
            </View>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Cân nặng (kg)</Text>
              <TextInput style={styles.input} keyboardType="numeric" placeholder="VD: 65" value={formData.weight?.toString()} onChangeText={(val) => updateField('weight', val)} />
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Huyết áp (mmHg)</Text>
              <TextInput style={styles.input} placeholder="VD: 120/80" value={formData.blood_pressure} onChangeText={(val) => updateField('blood_pressure', val)} />
            </View>
            <View style={styles.halfInput}>
              <Text style={styles.label}>Nhịp tim (lần/phút)</Text>
              <TextInput style={styles.input} keyboardType="numeric" placeholder="VD: 75" value={formData.heart_rate?.toString()} onChangeText={(val) => updateField('heart_rate', val)} />
            </View>
          </View>
          <View style={styles.fullInput}>
            <Text style={styles.label}>Nhiệt độ (°C) - Từ 30 đến 45</Text>
            <TextInput style={styles.input} keyboardType="numeric" placeholder="VD: 37.5" value={formData.temperature?.toString()} onChangeText={(val) => updateField('temperature', val)} />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📋 Lâm sàng & Chẩn đoán</Text>
          <Text style={styles.label}>Triệu chứng chính</Text>
          <TextInput style={[styles.input, styles.textArea]} multiline numberOfLines={3} placeholder="Bệnh nhân than phiền..." value={formData.symptom} onChangeText={(val) => updateField('symptom', val)} />
          <Text style={styles.label}>Tên bệnh / Chẩn đoán</Text>
          <TextInput style={styles.input} placeholder="VD: Viêm họng cấp" value={formData.disease_name} onChangeText={(val) => updateField('disease_name', val)} />
          <Text style={styles.label}>Kết luận / Hướng điều trị</Text>
          <TextInput style={[styles.input, styles.textArea]} multiline numberOfLines={3} placeholder="Nghỉ ngơi, uống nhiều nước..." value={formData.conclusion} onChangeText={(val) => updateField('conclusion', val)} />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📝 Ghi chú nội bộ</Text>
          <TextInput style={[styles.input, styles.textArea]} multiline numberOfLines={3} placeholder="Ghi chú dành cho bác sĩ..." value={formData.note} onChangeText={(val) => updateField('note', val)} />
        </View>

        <TouchableOpacity style={[styles.saveButton, isSubmitting && styles.saveButtonDisabled]} onPress={handleSaveRecord} disabled={isSubmitting}>
          {isSubmitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveButtonText}>💾 Lưu hồ sơ khám</Text>}
        </TouchableOpacity>
      </ScrollView>
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
  section: { backgroundColor: '#fff', padding: 16, marginHorizontal: 16, marginBottom: 16, borderRadius: 12 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#2f6fed', marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  halfInput: { width: '48%' },
  fullInput: { width: '100%' },
  label: { fontSize: 13, color: '#555', marginBottom: 6, fontWeight: '500' },
  input: { backgroundColor: '#f9f9f9', borderWidth: 1, borderColor: '#e0e0e0', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, color: '#111' },
  textArea: { textAlignVertical: 'top', minHeight: 80 },
  saveButton: { backgroundColor: '#2f6fed', margin: 16, paddingVertical: 16, borderRadius: 12, alignItems: 'center' },
  saveButtonDisabled: { backgroundColor: '#93b4f5' },
  saveButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});