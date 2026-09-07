import React from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { appointmentService } from '../../../services/appointmentService';
import { Payment } from '../../../types/appointment';

export default function PaymentHistoryScreen() {
  const router = useRouter();

  const { data: payments, isLoading, isError, refetch, isRefetching } = useQuery<Payment[]>({
    queryKey: ['myPayments'],
    queryFn: async () => {
      return await appointmentService.getMyPayments();
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusConfig = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PAID': return { label: 'Thành công', color: '#10b981', bg: '#d1fae5', icon: 'checkmark-circle' };
      case 'FAILED': return { label: 'Thất bại', color: '#ef4444', bg: '#fee2e2', icon: 'close-circle' };
      case 'PENDING': return { label: 'Đang xử lý', color: '#f59e0b', bg: '#fef3c7', icon: 'time' };
      default: return { label: 'Không rõ', color: '#6b7280', bg: '#f3f4f6', icon: 'help-circle' };
    }
  };

  const renderPaymentItem = ({ item }: { item: Payment }) => {
    const statusConfig = getStatusConfig(item.status);
    const summary = item.appointment_summary;

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.badgeContainer}>
            <Ionicons name={statusConfig.icon as any} size={16} color={statusConfig.color} />
            <Text style={[styles.badgeText, { color: statusConfig.color }]}>{statusConfig.label}</Text>
          </View>
          <Text style={styles.dateText}>{formatDate(item.created_date)}</Text>
        </View>

        <View style={styles.divider} />

        <View style={styles.cardBody}>
          <View style={{ flex: 1, paddingRight: 8 }}>
            <Text style={styles.label}>Nội dung thanh toán</Text>
            {/* ✅ SỬA: Hiển thị tên bác sĩ và chuyên khoa, có fallback nếu thiếu dữ liệu */}
            <Text style={styles.value} numberOfLines={2}>
              {summary 
                ? `Khám ${summary.specialty_name} - ${summary.doctor_name}`
                : `Lịch hẹn #${item.appointment_id}`
              }
            </Text>
            {summary && (
              <Text style={styles.subValue}>
                {new Date(summary.work_date).toLocaleDateString('vi-VN')} • {summary.start_time.substring(0, 5)}
              </Text>
            )}
          </View>
          
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={styles.label}>Số tiền</Text>
            <Text style={[styles.value, styles.amountText]}>{formatCurrency(item.amount)}</Text>
          </View>
        </View>

        {item.transaction_id && (
          <View style={styles.cardFooter}>
            <Ionicons name="receipt-outline" size={14} color="#9ca3af" />
            <Text style={styles.txnText}>Mã GD: {item.transaction_id}</Text>
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.center} edges={['top', 'bottom']}>
        <ActivityIndicator size="large" color="#2f6fed" />
        <Text style={styles.loadingText}>Đang tải lịch sử...</Text>
      </SafeAreaView>
    );
  }

  if (isError) {
    return (
      <SafeAreaView style={styles.center} edges={['top', 'bottom']}>
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text style={styles.errorText}>Không thể tải lịch sử thanh toán.</Text>
        <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
          <Text style={styles.retryText}>Thử lại</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <FlatList
        data={payments}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderPaymentItem}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={isRefetching}
        onRefresh={refetch}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="receipt-outline" size={64} color="#d1d5db" />
            <Text style={styles.emptyText}>Chưa có giao dịch nào</Text>
            <Text style={styles.emptySubText}>Lịch sử thanh toán của bạn sẽ hiển thị tại đây.</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loadingText: { marginTop: 12, color: '#666' },
  errorText: { color: '#c62828', marginBottom: 16, textAlign: 'center', fontSize: 15 },
  retryButton: { paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#e3f2fd', borderRadius: 8 },
  retryText: { color: '#2f6fed', fontWeight: '600' },
  
  listContent: { padding: 16 },
  
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  badgeContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f3f4f6', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20, gap: 6 },
  badgeText: { fontSize: 12, fontWeight: '600' },
  dateText: { fontSize: 12, color: '#6b7280' },
  
  divider: { height: 1, backgroundColor: '#f3f4f6', marginBottom: 12 },
  
  cardBody: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  label: { fontSize: 12, color: '#9ca3af', marginBottom: 4, textTransform: 'uppercase', fontWeight: '600' },
  value: { fontSize: 15, color: '#374151', fontWeight: '500' },
  amountText: { fontSize: 16, fontWeight: '700', color: '#2f6fed' },
  
  cardFooter: { flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 6 },
  txnText: { fontSize: 12, color: '#9ca3af', fontStyle: 'italic' },

  emptyContainer: { alignItems: 'center', marginTop: 60, paddingHorizontal: 32 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#6b7280', marginTop: 16 },
  emptySubText: { fontSize: 14, color: '#9ca3af', textAlign: 'center', marginTop: 8, lineHeight: 20 },
  subValue: { fontSize: 12, color: '#6b7280', marginTop: 2 }
});