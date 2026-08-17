// src/app/patient/appointments/index.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { appointmentService } from '../../../services/appointmentService';
import { AppointmentCard } from '../../../components/appointments/AppointmentCard';
import { Appointment } from '../../../types/appointment';

type TabType = 'upcoming' | 'history';

export default function PatientAppointmentsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('upcoming');
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAppointments = async (tab: TabType) => {
  setLoading(true);
  try {
    const allAppointments = await appointmentService.getMyAppointments();
    const now = new Date();
    const filtered = tab === 'upcoming'
      ? allAppointments.filter(a => new Date(a.startTime) > now)
      : allAppointments.filter(a => new Date(a.startTime) <= now);
    setAppointments(filtered);
  } catch (error) {
    console.error('Load appointments error:', error);
  } finally {
    setLoading(false);
  }
};

  useEffect(() => {
    loadAppointments(activeTab);
  }, [activeTab]);

  const handlePressAppointment = (appointmentId: string) => {
    router.push({
      pathname: '/patient/appointments/[appointmentId]',
      params: { appointmentId },
    });
  };

  return (
    <View style={styles.container}>
      {/* Segmented control */}
      <View style={styles.segmentedControl}>
        <TouchableOpacity
          style={[styles.segment, activeTab === 'upcoming' && styles.segmentActive]}
          onPress={() => setActiveTab('upcoming')}
        >
          <Text style={[styles.segmentText, activeTab === 'upcoming' && styles.segmentTextActive]}>
            Sắp tới
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.segment, activeTab === 'history' && styles.segmentActive]}
          onPress={() => setActiveTab('history')}
        >
          <Text style={[styles.segmentText, activeTab === 'history' && styles.segmentTextActive]}>
            Lịch sử
          </Text>
        </TouchableOpacity>
      </View>

      {/* Danh sách */}
      {loading ? (
        <ActivityIndicator style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={appointments}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <AppointmentCard
              appointment={item}
              onPress={() => handlePressAppointment(String(item.id))}
              variant="patient" // truyền variant để hiển thị đúng cho patient
            />
          )}
          ListEmptyComponent={
            <Text style={styles.emptyText}>
              {activeTab === 'upcoming' ? 'Không có lịch hẹn sắp tới.' : 'Không có lịch sử khám.'}
            </Text>
          }
          contentContainerStyle={{ padding: 16 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#e0e0e0',
    borderRadius: 10,
    margin: 16,
    padding: 4,
  },
  segment: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  segmentActive: {
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: { fontSize: 14, color: '#555' },
  segmentTextActive: { color: '#2f6fed', fontWeight: '600' },
  emptyText: { textAlign: 'center', marginTop: 40, color: '#888' },
});