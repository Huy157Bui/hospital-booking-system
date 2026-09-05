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

export default function ChangePasswordScreen() {
  const router = useRouter();
  const { logout } = useAuthStore();

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleChangePassword = async () => {
    if (newPassword.length < 6) {
      Alert.alert('Lỗi', 'Mật khẩu mới phải có ít nhất 6 ký tự');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Lỗi', 'Mật khẩu xác nhận không khớp với mật khẩu mới');
      return;
    }
    if (!oldPassword) {
      Alert.alert('Lỗi', 'Vui lòng nhập mật khẩu hiện tại');
      return;
    }

    setLoading(true);
    try {
      await userService.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });

      Alert.alert('Thành công', 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.', [
        { 
          text: 'Đồng ý', 
          onPress: async () => {
            await logout();
            router.replace('/(auth)/login');
          } 
        }
      ]);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Mật khẩu cũ không đúng hoặc có lỗi xảy ra';
      Alert.alert('Lỗi', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const renderPasswordInput = (value: string, onChangeText: (text: string) => void, placeholder: string, show: boolean, setShow: (show: boolean) => void) => (
    <View style={styles.inputWrapper}>
      <TextInput style={styles.input} value={value} onChangeText={onChangeText} placeholder={placeholder} secureTextEntry={!show} autoCapitalize="none" />
      <TouchableOpacity onPress={() => setShow(!show)} style={styles.eyeButton}>
        <Ionicons name={show ? "eye" : "eye-off"} size={22} color="#666" />
      </TouchableOpacity>
    </View>
  );

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
          <Text style={styles.headerTitle}>Đổi mật khẩu</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.formGroup}>
            <Text style={styles.label}>Mật khẩu hiện tại</Text>
            {renderPasswordInput(oldPassword, setOldPassword, "Nhập mật khẩu cũ", showOld, setShowOld)}
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Mật khẩu mới (tối thiểu 6 ký tự)</Text>
            {renderPasswordInput(newPassword, setNewPassword, "Nhập mật khẩu mới", showNew, setShowNew)}
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Xác nhận mật khẩu mới</Text>
            {renderPasswordInput(confirmPassword, setConfirmPassword, "Nhập lại mật khẩu mới", showConfirm, setShowConfirm)}
          </View>

          <TouchableOpacity style={[styles.saveButton, loading && styles.saveButtonDisabled]} onPress={handleChangePassword} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveButtonText}>Đổi mật khẩu</Text>}
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
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 10 },
  input: { flex: 1, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: '#333' },
  eyeButton: { paddingHorizontal: 16, paddingVertical: 14, justifyContent: 'center', alignItems: 'center' },
  saveButton: { backgroundColor: '#2f6fed', paddingVertical: 16, borderRadius: 10, alignItems: 'center', marginTop: 20 },
  saveButtonDisabled: { backgroundColor: '#a0b4f0' },
  saveButtonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});