import { SafeAreaView, StyleSheet, View } from 'react-native';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { AppPageHeader } from '../../../components/navigation/AppPageHeader';
import { DsButton, DsCard, DsText } from '../../../components/design-system';
import { colors, spacing } from '../../../theme';
import type { RideBooking } from '../data/bookingApi';

type BookingStatusScreenProps = { ride: RideBooking; onDone: () => void; onMenuPress: () => void };
export function BookingStatusScreen({ ride, onDone, onMenuPress }: BookingStatusScreenProps) { return <SafeAreaView style={styles.safe}><View style={styles.content}><AppPageHeader onBack={onDone} onMenuPress={onMenuPress} title="Ride request" /><View style={styles.body}><View style={styles.icon}><MaterialCommunityIcons color={colors.primary} name="radar" size={52} /></View><DsText color={colors.primary} variant="display" style={styles.center}>Finding your driver</DsText><DsText color={colors.textSecondary} style={styles.center}>Your request is ready for nearby drivers to accept.</DsText><DsCard elevated style={styles.card}><DsText variant="h3">{ride.pickup_address}</DsText><DsText color={colors.textTertiary}>to</DsText><DsText variant="h3">{ride.destination_address}</DsText><DsText color={colors.primary} variant="h2">₹ {ride.fare_paise / 100}</DsText></DsCard><DsButton label="Back to Home" onPress={onDone} size="large" /></View></View></SafeAreaView>; }
const styles = StyleSheet.create({ safe: { backgroundColor: colors.background, flex: 1 }, content: { flex: 1, gap: spacing.xl, padding: spacing.xl }, body: { flex: 1, gap: spacing.xl, justifyContent: 'center' }, icon: { alignItems: 'center' }, center: { textAlign: 'center' }, card: { gap: spacing.sm } });
