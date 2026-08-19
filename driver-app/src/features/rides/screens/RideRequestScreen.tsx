import { useEffect, useState } from 'react';
import { Alert, SafeAreaView, ScrollView, StyleSheet, View } from 'react-native';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { DriverPageHeader } from '../../../components/DriverPageHeader';
import { DriverButton } from '../../../components/DriverButton';
import { DriverCard } from '../../../components/DriverCard';
import { DriverText } from '../../../components/DriverText';
import { colors, radius, spacing } from '../../../theme';
import { rideMatchingService, type DriverRideOffer } from '../services/rideMatchingService';
import { driverRealtimeService } from '../services/driverRealtimeService';
import { useDriverSession } from '../../dashboard/state/DriverSessionContext';

type RideRequestScreenProps = { onBack: () => void; onAccepted: () => void };
export function RideRequestScreen({ onBack, onAccepted }: RideRequestScreenProps) {
  const { isOnline, setRequestStatus } = useDriverSession();
  const [request, setRequest] = useState<DriverRideOffer | null>(null);
  const [message, setMessage] = useState('');
  const [liveConnected, setLiveConnected] = useState(false);
  useEffect(() => driverRealtimeService.subscribe(event => {
    if (event.type === 'ride.offer') {
      setRequest(event.data);
      setMessage('');
    } else {
      setRequest(null);
    }
  }, setLiveConnected), []);
  useEffect(() => {
    if (liveConnected) return;
    const load = () => void rideMatchingService.getCurrentOffer().then(setRequest).catch(() => { setMessage('Unable to load ride offers.'); setRequest(null); });
    load();
    const interval = setInterval(load, 10_000);
    return () => clearInterval(interval);
  }, [liveConnected]);
  const unavailable = !isOnline;
  const actOnRequest = async (status: 'accepted' | 'declined') => { try { const result = await rideMatchingService.respond(request!.offer_id, status); setRequestStatus(status); Alert.alert(status === 'accepted' ? 'Ride accepted' : 'Ride declined', result.message, [{ text: status === 'accepted' ? 'Track pickup' : 'Done', onPress: status === 'accepted' ? onAccepted : onBack }]); } catch { setMessage('This offer is no longer available. We will keep checking for another ride.'); setRequest(null); } };
  return <SafeAreaView style={styles.safe}><DriverPageHeader onBack={onBack} title="Ride Request"/><ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>{message ? <DriverText color={colors.error}>{message}</DriverText> : null}{!request ? <DriverCard style={styles.unavailable}><DriverText color={colors.textSecondary} style={styles.center}>No ride request is available right now.</DriverText></DriverCard> : <><DriverText color={colors.textSecondary}>Review the request before responding.</DriverText><DriverCard style={styles.route}><RouteRow address={request.pickup_address} icon="map-marker" label="Pickup location"/><RouteRow address={request.destination_address} icon="map-marker-check" label="Drop location"/></DriverCard><DriverCard style={styles.fare}><View><DriverText color={colors.textSecondary}>Estimated distance</DriverText><DriverText size={24} weight="700">{request.estimated_distance_km} km</DriverText></View><View><DriverText color={colors.textSecondary}>Expected fare</DriverText><DriverText color={colors.primary} size={28} weight="700">₹{Math.round(request.expected_fare_paise / 100)}</DriverText></View></DriverCard><DriverCard style={styles.note}><MaterialCommunityIcons color={colors.primary} name="clock-outline" size={25}/><DriverText color={colors.textSecondary} style={styles.noteCopy}>Please respond within 15 seconds. Pickup is approximately {request.pickup_minutes_away} minutes away.</DriverText></DriverCard>{unavailable ? <DriverCard style={styles.unavailable}><DriverText color={colors.textSecondary} style={styles.center}>{!isOnline ? 'Go online to receive and accept requests.' : 'This request has already been handled.'}</DriverText></DriverCard> : <View style={styles.actions}><DriverButton label="Decline" onPress={() => void actOnRequest('declined')} variant="secondary"/><DriverButton label="Accept Ride" onPress={() => void actOnRequest('accepted')}/></View>}</>}</ScrollView></SafeAreaView>;
}
function RouteRow({ address, icon, label }: { address: string; icon: string; label: string }) { return <View style={styles.routeRow}><View style={styles.routeIcon}><MaterialCommunityIcons color={colors.white} name={icon} size={21}/></View><View style={styles.routeCopy}><DriverText color={colors.textSecondary} size={14}>{label}</DriverText><DriverText size={20} weight="500">{address}</DriverText></View></View>; }
const styles = StyleSheet.create({ safe: { backgroundColor: colors.background, flex: 1 }, content: { gap: spacing.lg, padding: spacing.xl, paddingBottom: spacing.massive }, route: { gap: spacing.md, padding: spacing.lg }, routeRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.md }, routeIcon: { alignItems: 'center', backgroundColor: colors.primary, borderRadius: radius.pill, height: 32, justifyContent: 'center', width: 32 }, routeCopy: { flex: 1, gap: spacing.xxs }, fare: { flexDirection: 'row', justifyContent: 'space-between', padding: spacing.lg }, note: { alignItems: 'center', backgroundColor: colors.primarySoft, flexDirection: 'row', gap: spacing.sm, padding: spacing.md }, noteCopy: { flex: 1 }, actions: { flexDirection: 'row', gap: spacing.md }, unavailable: { padding: spacing.lg }, center: { textAlign: 'center' } });
