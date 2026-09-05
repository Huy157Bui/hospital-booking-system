import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, TouchableOpacity, TextInput, 
  Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../../store/useAuthStore';
import { userService } from '../../../services/userService';
import { Ionicons } from '@expo/vector-icons';

export default function EditProfileScreen() {
  const router = useRouter();
  const { user, setUser } = useAuthStore();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [email, setEmail] = useState(user?.email || '');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!fullName.trim()) {
      Alert.alert('Lỗi', 'Họ và tên không được để trống');
      return;
    }

    const phoneRegex = /^(0|\+84)(3|5|7|8|9)[0-9]{8}$/;
    if (phone && !phoneRegex.test(phone)) {
      Alert.alert('Lỗi', 'Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 số (VD: 0912345678)');
      return;
    }

    setLoading(true);
    try {
      const updatedUser = await userService.updateMe({
        full_name: fullName.trim(),
        phone: phone.trim(),
        email: email.trim(),
      });

      if (setUser) setUser(updatedUser);

      Alert.alert('Thành công', 'Cập nhật thông tin thành công!', [
        { text: 'OK', onPress: () => router.replace('/(patient)/profile') }
      ]);
    } catch (error: any) {
      let errorMsg = 'Không thể cập nhật thông tin. Vui lòng thử lại.';
      
      if (error.response?.status === 422) {
        const details = error.response?.data?.detail;
        if (Array.isArray(details) && details.length > 0) {
          const firstError = details[0];
          const location = firstError.loc;
          
          if (location?.includes('email')) {
            errorMsg = 'Email không hợp lệ. Vui lòng nhập đúng định dạng (ví dụ: abc@gmail.com)';
          } else if (location?.includes('phone')) {
            errorMsg = 'Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 số (ví dụ: 0912345678)';
          } else if (location?.includes('full_name')) {
            errorMsg = 'Họ và tên không được để trống';
          } else {
            errorMsg = firstError.msg || 'Dữ liệu không hợp lệ';
            if (errorMsg.toLowerCase().includes('regex') || errorMsg.toLowerCase().includes('string')) {
               errorMsg = 'Định dạng dữ liệu không đúng. Vui lòng kiểm tra lại.';
            }
          }
        } else if (typeof details === 'string') {
          errorMsg = details;
        }
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      }
      
      Alert.alert('Lỗi', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={styles.customHeader}>
          <TouchableOpacity 
            onPress={() => router.replace('/(patient)/profile')} 
            style={styles.backButton} 
            activeOpacity={0.7}
          >
            <Ionicons name="arrow-back" size={24} color="#333" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Sửa thông tin</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.formGroup}>
            <Text style={styles.label}>Họ và tên</Text>
            <TextInput style={styles.input} value={fullName} onChangeText={setFullName} placeholder="Nhập họ và tên" autoCapitalize="words" />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Số điện thoại</Text>
            <TextInput style={styles.input} value={phone} onChangeText={setPhone} placeholder="Nhập số điện thoại" keyboardType="phone-pad" />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Email</Text>
            <TextInput style={styles.input} value={email} onChangeText={setEmail} placeholder="Nhập địa chỉ email" keyboardType="email-address" autoCapitalize="none" />
          </View>

          <TouchableOpacity style={[styles.saveButton, loading && styles.saveButtonDisabled]} onPress={handleSave} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveButtonText}>Lưu thay đổi</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f5f5' },
  container: { flex: 1 },
  customHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  backButton: { padding: 8, marginLeft: -8 },
  headerTitle: { fontSize: 18, fontWeight: '600', color: '#333' },
  scrollContent: { padding: 20 },
  formGroup: { marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 8 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 10, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: '#333' },
  saveButton: { backgroundColor: '#2f6fed', paddingVertical: 16, borderRadius: 10, alignItems: 'center', marginTop: 20 },
  saveButtonDisabled: { backgroundColor: '#a0b4f0' },
  saveButtonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});