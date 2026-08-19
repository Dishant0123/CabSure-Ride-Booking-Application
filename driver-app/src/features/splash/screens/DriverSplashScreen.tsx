import { SafeAreaView, StyleSheet, View } from 'react-native';
import { DriverBrandMark } from '../../../components/brand/DriverBrandMark';
import { DriverButton } from '../../../components/DriverButton';
import { DriverText } from '../../../components/DriverText';
import { colors, spacing } from '../../../theme';

export function DriverSplashScreen({ onContinue }: { onContinue: () => void }) { return <SafeAreaView style={styles.safe}><View style={styles.content}><View style={styles.hero}><DriverBrandMark size={118}/><DriverText color={colors.primary} size={32} weight="700">Welcome</DriverText><DriverText color={colors.textSecondary} style={styles.subtitle}>Drive with confidence. Grow with CabSure.</DriverText></View><DriverButton label="Continue" onPress={onContinue}/></View></SafeAreaView>; }
const styles = StyleSheet.create({ safe: { backgroundColor: colors.surface, flex: 1 }, content: { flex: 1, justifyContent: 'space-between', padding: spacing.xxl }, hero: { alignItems: 'center', gap: spacing.lg, marginTop: '45%' }, subtitle: { textAlign: 'center' } });
