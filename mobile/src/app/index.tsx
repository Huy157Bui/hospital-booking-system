import { Redirect } from 'expo-router';
import { useAuthStore } from '../store/useAuthStore';

export default function Index() {
  const { isAuthenticated, role } = useAuthStore();

  if (!isAuthenticated) {
    return <Redirect href="/auth/login" />;
  }

  if (role === 'doctor') {
    return <Redirect href="/doctor/today" />;
  }

  return <Redirect href="/patient/home" />;
}