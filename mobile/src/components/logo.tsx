import { StyleSheet, Text, View } from 'react-native';

export default function Logo() {
  return (
    <View style={styles.logoBadge}>
      <Text style={styles.logoEmoji}>🏥</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  logoBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.25)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  logoEmoji: {
    fontSize: 36,
  },
});