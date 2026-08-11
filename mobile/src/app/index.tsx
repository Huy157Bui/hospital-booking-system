import { Redirect } from 'expo-router';
import { useAuthStore } from '../store/useAuthStore';

export default function Index() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Nếu đã Đăng nhập -> Chuyển vào trang /tabs
  if (isAuthenticated) {
    return <Redirect href="/tabs" />;
  }

  // Nếu Chưa đăng nhập -> Chuyển vào trang /auth/login
  return <Redirect href="/auth/login" />;
}