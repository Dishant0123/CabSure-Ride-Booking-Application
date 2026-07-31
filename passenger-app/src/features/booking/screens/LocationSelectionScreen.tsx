import { useEffect, useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, View } from 'react-native';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

import { DsButton, DsCard, DsEmptyState, DsLoading, DsText } from '../../../components/design-system';
import { AppPageHeader } from '../../../components/navigation/AppPageHeader';
import { colors, spacing } from '../../../theme';
import { bookingApi, type LocationOption } from '../data/bookingApi';

type LocationSelectionScreenProps = { title: string; onBack: () => void; onMenuPress: () => void; onSelected: (location: LocationOption) => void | Promise<void> };

/** Explicit location decision step shared by pickup, destination, and saved-place editing. */
export function LocationSelectionScreen({ title, onBack, onMenuPress, onSelected }: LocationSelectionScreenProps) {
  const [locations, setLocations] = useState<LocationOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<LocationOption | null>(null);
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => { void bookingApi.locations().then(setLocations).catch(() => setError('Unable to load locations.')); }, []);
  if (error) return <SafeAreaView style={styles.safe}><DsEmptyState actionLabel="Back" onAction={onBack} title={error} /></SafeAreaView>;
  if (!locations.length) return <SafeAreaView style={styles.safe}><DsLoading fullScreen label="Loading locations…" /></SafeAreaView>;
  const confirm = async () => { if (!selected) return; setSubmitting(true); try { await onSelected(selected); } catch { setError('Unable to save this location. Please try again.'); } finally { setSubmitting(false); } };
  return <SafeAreaView style={styles.safe}><View style={styles.screen}><ScrollView contentContainerStyle={styles.content}><AppPageHeader onBack={onBack} onMenuPress={onMenuPress} title={title} /><DsText color={colors.textSecondary}>Choose one available demo location, then confirm your choice.</DsText>{locations.map(location => <Pressable key={location.id} onPress={() => setSelected(location)}><DsCard elevated style={[styles.item, selected?.id === location.id && styles.selectedItem]}><MaterialCommunityIcons color={colors.primary} name="map-marker" size={28} /><View style={styles.copy}><DsText variant="h3">{location.name}</DsText><DsText color={colors.textSecondary}>{location.formatted_address}</DsText></View><MaterialCommunityIcons color={selected?.id === location.id ? colors.primary : colors.textTertiary} name={selected?.id === location.id ? 'check-circle' : 'circle-outline'} size={24} /></DsCard></Pressable>)}</ScrollView><View style={styles.footer}><DsButton disabled={!selected} label="Next" loading={submitting} onPress={confirm} /></View></View></SafeAreaView>;
}
const styles = StyleSheet.create({ safe: { backgroundColor: colors.background, flex: 1 }, screen: { flex: 1 }, content: { gap: spacing.lg, padding: spacing.xl, paddingBottom: spacing.xxl }, item: { alignItems: 'center', flexDirection: 'row', gap: spacing.md }, selectedItem: { borderColor: colors.primary, borderWidth: 1.5, shadowColor: colors.primaryShadow, shadowOpacity: 1, shadowRadius: 12 }, copy: { flex: 1, gap: spacing.xs }, footer: { backgroundColor: colors.surface, borderTopColor: colors.border, borderTopWidth: 1, padding: spacing.xl } });
