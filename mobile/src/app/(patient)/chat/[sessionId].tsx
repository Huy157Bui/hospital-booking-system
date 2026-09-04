import { View, Text, StyleSheet } from 'react-native';

export default function PlaceholderScreen({ routeName }: { routeName?: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>🚧 Màn hình đang phát triển</Text>
      {routeName && <Text style={styles.subText}>({routeName})</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5' },
  text: { fontSize: 16, fontWeight: '600', color: '#333' },
  subText: { fontSize: 14, color: '#666', marginTop: 8 }
});