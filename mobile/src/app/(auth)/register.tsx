import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { useAuthStore } from '../../store/useAuthStore';
import Logo from '../../components/logo';

export default function RegisterScreen() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const register = useAuthStore((state) => state.register);
  const router = useRouter();

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !fullName.trim() || !password.trim()) {
      Alert.alert('Thông báo', 'Vui lòng điền đầy đủ thông tin');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      Alert.alert('Thông báo', 'Email không đúng định dạng');
      return;
    }

    if (password.length < 8) {
      Alert.alert('Thông báo', 'Mật khẩu phải chứa ít nhất 8 ký tự');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        username,
        email,
        full_name: fullName,
        password,
      });
      Alert.alert('Thành công', 'Đăng ký tài khoản thành công', [
        { text: 'OK', onPress: () => router.push('/(auth)/login') },
      ]);
    } catch (error: any) {
      Alert.alert('Đăng ký thất bại', error.message || 'Có lỗi xảy ra');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <BlurView intensity={80} tint="light" style={styles.glassContainer}>
          <View style={styles.headerContainer}>
            <Logo />
          </View>

          <View style={styles.formInner}>
            <TextInput
              style={styles.input}
              placeholder="Tên đăng nhập"
              placeholderTextColor="rgba(22, 163, 74, 0.5)"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
            />

            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor="rgba(22, 163, 74, 0.5)"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <TextInput
              style={styles.input}
              placeholder="Họ và tên"
              placeholderTextColor="rgba(22, 163, 74, 0.5)"
              value={fullName}
              onChangeText={setFullName}
            />

            <TextInput
              style={styles.input}
              placeholder="Mật khẩu"
              placeholderTextColor="rgba(22, 163, 74, 0.5)"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            <TouchableOpacity
              style={[styles.button, isSubmitting && styles.buttonDisabled]}
              onPress={handleRegister}
              disabled={isSubmitting}
              activeOpacity={0.8}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.buttonText}>ĐĂNG KÝ</Text>
              )}
            </TouchableOpacity>

            <View style={styles.footerContainer}>
              <Text style={styles.footerText}>Đã có tài khoản? </Text>
              <TouchableOpacity onPress={() => router.back()}>
                <Text style={styles.loginText}>Đăng nhập ngay</Text>
              </TouchableOpacity>
            </View>
          </View>
        </BlurView>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0fdf4',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  glassContainer: {
    width: '100%',
    maxWidth: 400,
    borderRadius: 24,
    padding: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.55)',
    overflow: 'hidden',
    borderWidth: 0,
    borderColor: 'transparent',
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  headerContainer: {
    alignItems: 'center',
    marginBottom: 28,
  },
  formInner: {
    width: '100%',
  },
  input: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 17,
    color: '#15803d',
    marginBottom: 16,
    borderWidth: 0,
    borderColor: 'transparent',
  },
  button: {
    backgroundColor: '#16a34a',
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    backgroundColor: '#86efac',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  footerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
  footerText: {
    fontSize: 14,
    color: '#14532d',
  },
  loginText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#15803d',
  },
});