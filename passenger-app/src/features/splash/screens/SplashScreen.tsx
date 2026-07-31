import { SafeAreaView, StyleSheet, View } from 'react-native';

import { BrandMark } from '../../../components/auth/BrandMark';
import { DsButton, DsText } from '../../../components/design-system';
import { colors, spacing } from '../../../theme';

type SplashScreenProps = { onContinue: () => void };

/** First-launch screen; it deliberately has one action that transitions into authentication. */
export function SplashScreen({ onContinue }: SplashScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.content}>
        <View style={styles.hero}>
          <BrandMark size={112} />
          <DsText color={colors.primary} variant="display">Cab Sure</DsText>
          <DsText color={colors.textSecondary} style={styles.subtitle}>Made in IIT-DH</DsText>
        </View>
        <DsButton label="Continue" onPress={onContinue} size="large" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.surface, flex: 1 },
  content: { flex: 1, justifyContent: 'space-between', padding: spacing.xxl },
  hero: { alignItems: 'center', gap: spacing.lg, marginTop: '45%' },
  subtitle: { textAlign: 'center' },
});
