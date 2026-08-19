import { Pressable, StyleSheet, View } from 'react-native';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { DriverText } from '../../../components/DriverText';
import { colors, radius, shadows, spacing } from '../../../theme';

export function DriverHeader({ fullName, onMenuPress, onRequestPress }: { fullName: string; onMenuPress: () => void; onRequestPress: () => void }) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  return <View style={styles.header}><View style={styles.identity}><View style={styles.avatar}><MaterialCommunityIcons color={colors.primary} name="account" size={30} /></View><View><DriverText color={colors.primary} size={28} weight="700">Hello, {fullName}</DriverText><DriverText color={colors.textSecondary}>{greeting}</DriverText></View></View><View style={styles.actions}><Pressable accessibilityLabel="View ride request" onPress={onRequestPress} style={styles.action}><MaterialCommunityIcons color={colors.primary} name="bell-outline" size={25} /></Pressable><Pressable accessibilityLabel="Open menu" onPress={onMenuPress} style={styles.action}><MaterialCommunityIcons color={colors.primary} name="menu" size={27} /></Pressable></View></View>;
}
const styles = StyleSheet.create({ header: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' }, identity: { alignItems: 'center', flex: 1, flexDirection: 'row', gap: spacing.md }, actions: { flexDirection: 'row', gap: spacing.xs }, avatar: { alignItems: 'center', backgroundColor: colors.primarySoft, borderColor: colors.primary, borderRadius: radius.pill, borderWidth: 1, height: 54, justifyContent: 'center', width: 54 }, action: { ...shadows.card, alignItems: 'center', backgroundColor: colors.white, borderColor: colors.primary, borderRadius: radius.md, borderWidth: 1, height: 48, justifyContent: 'center', width: 48 } });
