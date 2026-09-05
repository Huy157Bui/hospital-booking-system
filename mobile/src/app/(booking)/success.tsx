import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function BookingSuccessScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const insets = useSafeAreaInsets();

  const doctorName = (params.doctorName as string) || 'Bác sĩ';
  const specialty = (params.specialty as string) || 'Chuyên khoa';
  const date = (params.date as string) || '...';
  const time = (params.time as string) || '...';
  const appointmentId = (params.appointmentId as string) || '...';

  const formatDate = (dateStr: string) => {
    if (dateStr === '...') return dateStr;
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.iconContainer}>
          <Ionicons name="checkmark-circle" size={80} color="#10b981" />
        </View>

        <Text style={styles.title}>Đặt lịch thành công!</Text>
        <Text style={styles.subtitle}>
          Lịch khám của bạn đã được ghi nhận. Vui lòng đến đúng giờ để được hỗ trợ tốt nhất.
        </Text>

        <View style={styles.card}>
          <View style={styles.row}>
            <Ionicons name="person" size={20} color="#4b5563" />
            <View style={styles.rowText}>
              <Text style={styles.label}>Bác sĩ</Text>
              <Text style={styles.value}>{doctorName}</Text>
            </View>
          </View>
          
          <View style={styles.divider} />

          <View style={styles.row}>
            <Ionicons name="medical" size={20} color="#4b5563" />
            <View style={styles.rowText}>
              <Text style={styles.label}>Chuyên khoa</Text>
              <Text style={styles.value}>{specialty}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <Ionicons name="calendar" size={20} color="#4b5563" />
            <View style={styles.rowText}>
              <Text style={styles.label}>Ngày khám</Text>
              <Text style={styles.value}>{formatDate(date)}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <Ionicons name="time" size={20} color="#4b5563" />
            <View style={styles.rowText}>
              <Text style={styles.label}>Giờ khám</Text>
              <Text style={styles.value}>{time}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <Ionicons name="ticket" size={20} color="#4b5563" />
            <View style={styles.rowText}>
              <Text style={styles.label}>Mã lịch hẹn</Text>
              <Text style={[styles.value, { color: '#2563eb', fontWeight: 'bold' }]}>
                #{appointmentId}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.primaryButton}
            onPress={() => router.replace('/(patient)/appointments')}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryButtonText}>Xem danh sách lịch hẹn</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={() => router.replace('/(patient)/home')}
            activeOpacity={0.8}
          >
            <Text style={styles.secondaryButtonText}>Về trang chủ</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f8fafc' 
  },
  scrollContent: { 
    flexGrow: 1,
    padding: 24, 
    alignItems: 'center', 
    justifyContent: 'center',
    paddingBottom: 40
  },
  iconContainer: { 
    marginBottom: 24 
  },
  title: { 
    fontSize: 24, 
    fontWeight: 'bold', 
    color: '#111827', 
    marginBottom: 8, 
    textAlign: 'center' 
  },
  subtitle: { 
    fontSize: 15, 
    color: '#6b7280', 
    textAlign: 'center', 
    marginBottom: 32, 
    lineHeight: 22 
  },
  card: {
    width: '100%', 
    backgroundColor: '#ffffff', 
    borderRadius: 16, 
    padding: 20,
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 4 }, 
    shadowOpacity: 0.05, 
    shadowRadius: 8, 
    elevation: 3, 
    marginBottom: 32,
  },
  row: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingVertical: 8 
  },
  rowText: { 
    marginLeft: 16, 
    flex: 1 
  },
  label: { 
    fontSize: 13, 
    color: '#6b7280', 
    marginBottom: 2 
  },
  value: { 
    fontSize: 16, 
    color: '#111827', 
    fontWeight: '600' 
  },
  divider: { 
    height: 1, 
    backgroundColor: '#f3f4f6', 
    marginVertical: 8 
  },
  buttonContainer: { 
    width: '100%', 
    gap: 12 
  },
  primaryButton: {
    backgroundColor: '#2563eb', 
    paddingVertical: 16, 
    borderRadius: 12, 
    alignItems: 'center',
    shadowColor: '#2563eb', 
    shadowOffset: { width: 0, height: 4 }, 
    shadowOpacity: 0.2, 
    shadowRadius: 8, 
    elevation: 4,
  },
  primaryButtonText: { 
    color: '#ffffff', 
    fontSize: 16, 
    fontWeight: 'bold' 
  },
  secondaryButton: {
    backgroundColor: '#ffffff', 
    paddingVertical: 16, 
    borderRadius: 12, 
    alignItems: 'center', 
    borderWidth: 1, 
    borderColor: '#e5e7eb',
  },
  secondaryButtonText: { 
    color: '#374151', 
    fontSize: 16, 
    fontWeight: '600' 
  },
});