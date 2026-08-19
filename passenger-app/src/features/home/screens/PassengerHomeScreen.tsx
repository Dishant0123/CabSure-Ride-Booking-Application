import { useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, View } from 'react-native';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

import {
  DsButton,
  DsCard,
  DsEmptyState,
  DsLoading,
  DsText,
} from '../../../components/design-system';
import { colors, radius, shadows, spacing } from '../../../theme';
import type { LocationOption } from '../../booking/data/bookingApi';
import { authService } from '../../auth/services/authService';
import { HomeDrawer } from '../components/HomeDrawer';
import type { DrawerDestination } from '../components/HomeDrawer';
import { ImagePlaceholder } from '../components/ImagePlaceholder';
import { LocationCard } from '../components/LocationCard';
import { RideOptionCard } from '../components/RideOptionCard';
import type { RecentRide, SavedPlace } from '../domain/homeTypes';
import { usePassengerHome } from '../state/usePassengerHome';
import profileImage from '../../../assets/images/profile.png';
import carImage from '../../../assets/images/car.png';
import bikeImage from '../../../assets/images/bike.png';
import autoImage from '../../../assets/images/auto.png';

type PassengerHomeScreenProps = {
  pickup: LocationOption | null;
  destination: LocationOption | null;
  onLogout: () => void;
  onSelectPickup: () => void;
  onSelectDestination: () => void;
  onEditSavedPlace: (place: SavedPlace) => void;
  onContinueToFare: (categoryId: number) => void;
  onMenuNavigate: (destination: DrawerDestination) => void;
  onBookInstantRide: () => void;
  onBookOutstation: () => void;
  onOpenNotifications: () => void;
  activeRideId?: number | null;
  onResumeRide?: () => void;
};

/** Passenger home */
export function PassengerHomeScreen({
  pickup,
  destination,
  onLogout,
  onSelectPickup,
  onSelectDestination,
  onEditSavedPlace,
  onContinueToFare,
  onMenuNavigate,
  onBookInstantRide,
  onBookOutstation,
  onOpenNotifications,
  activeRideId,
  onResumeRide,
}: PassengerHomeScreenProps) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const { data, error, loading, refresh } = usePassengerHome();
  const logout = async () => {
    await authService.clearSession();
    setMenuVisible(false);
    onLogout();
  };
  if (loading)
    return (
      <SafeAreaView style={styles.safeArea}>
        <DsLoading fullScreen label="Loading your ride options…" />
      </SafeAreaView>
    );
  if (error || !data)
    return (
      <SafeAreaView style={styles.safeArea}>
        <DsEmptyState
          actionLabel="Try again"
          description={error ?? 'No Home data is available.'}
          onAction={() => void refresh()}
          title="Unable to load Home"
        />
      </SafeAreaView>
    );
  const canContinue = !!pickup && !!destination && !!selectedCategoryId;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.greeting}>
            <ImagePlaceholder label="Profile" source={profileImage} style={styles.avatar} />
            <View>
              <DsText color={colors.textTertiary} variant="body">
                Good Morning,
              </DsText>
              <DsText color={colors.primary} variant="display" style={styles.name}>
                Dishant
              </DsText>
            </View>
          </View>
          <View style={styles.headerActions}>
            <HeaderAction icon="bell-outline" onPress={onOpenNotifications} />
            <HeaderAction icon="menu" onPress={() => setMenuVisible(true)} />
          </View>
        </View>
        <LocationCard
          destination={destination}
          onDestinationPress={onSelectDestination}
          onPickupPress={onSelectPickup}
          pickup={pickup}
        />
        {activeRideId ? <Pressable accessibilityRole="button" onPress={onResumeRide}><DsCard elevated style={styles.activeRide}><View style={styles.safetyIcon}><MaterialCommunityIcons color={colors.primary} name="navigation-variant" size={28}/></View><View style={styles.safetyCopy}><DsText color={colors.primary} variant="bodyMedium">Continue active ride #{activeRideId}</DsText><DsText color={colors.textSecondary} variant="caption">Return to live Driver tracking and ride controls.</DsText></View><MaterialCommunityIcons color={colors.primary} name="chevron-right" size={24}/></DsCard></Pressable> : null}
        <SectionTitle action="Manage" onAction={() => onMenuNavigate('addresses')} title="Saved places" />
        <DsCard elevated style={styles.savedPlaces}>
          {['Home', 'Work'].map((label) => (
            <SavedPlaceCard
              key={label}
              place={data.saved_places.find((item) => item.label === label)}
              onPress={() => {
                const place = data.saved_places.find((item) => item.label === label);
                if (place) onEditSavedPlace(place);
              }}
            />
          ))}
        </DsCard>
        <SectionTitle action="Tap a vehicle" title="Choose a ride" />
        <View style={styles.rideRow}>
          {data.ride_categories.map((category) => (
            <RideOptionCard
              eta={`${category.estimated_arrival_minutes} min away`}
              fare={(category.base_fare_paise / 100).toString()}
              imageSource={vehicleImages[category.code as keyof typeof vehicleImages]}
              key={category.id}
              name={category.display_name}
              onPress={() => setSelectedCategoryId(category.id)}
              selected={selectedCategoryId === category.id}
            />
          ))}
        </View>
        {canContinue && (
          <DsButton
            label="View fare estimate"
            onPress={() => onContinueToFare(selectedCategoryId)}
          />
        )}
        <Pressable accessibilityHint="Opens customer support for a manual ride booking" accessibilityLabel="Book instant ride" accessibilityRole="button" onPress={onBookInstantRide}>
        <DsCard elevated style={styles.safetyCard}>
          <View style={styles.safetyIcon}>
            <MaterialCommunityIcons color={colors.primary} name="phone-in-talk-outline" size={28} />
          </View>
          <View style={styles.safetyCopy}>
            <DsText variant="bodyMedium">Book instant ride</DsText>
            <DsText color={colors.textTertiary} variant="caption">
              Call CabSure Support to arrange a ride with our team.
            </DsText>
          </View>
          <MaterialCommunityIcons color={colors.primary} name="chevron-right" size={24} />
        </DsCard>
        </Pressable>
        <Pressable accessibilityHint="Opens the future long-distance booking form" accessibilityLabel="Book outstation ride" accessibilityRole="button" onPress={onBookOutstation}>
          <DsCard elevated style={styles.safetyCard}>
            <View style={styles.safetyIcon}>
              <MaterialCommunityIcons color={colors.primary} name="road-variant" size={28} />
            </View>
            <View style={styles.safetyCopy}>
              <DsText variant="bodyMedium">Outstation ride booking</DsText>
              <DsText color={colors.textTertiary} variant="caption">Schedule travel beyond 150 km. Support confirms fare and driver.</DsText>
            </View>
            <MaterialCommunityIcons color={colors.primary} name="chevron-right" size={24} />
          </DsCard>
        </Pressable>
        <SectionTitle action="See all" onAction={() => onMenuNavigate('rides')} title="Recent rides" />
        <View style={styles.recentList}>
          {data.recent_rides.map((ride) => (
            <RecentRide key={ride.id} ride={ride} />
          ))}
        </View>
      </ScrollView>
      <HomeDrawer
        activeDestination="home"
        onClose={() => setMenuVisible(false)}
        onLogout={logout}
        onNavigate={(destination) => {
          setMenuVisible(false);
          onMenuNavigate(destination);
        }}
        visible={menuVisible}
      />
    </SafeAreaView>
  );
}

function HeaderAction({ icon, onPress }: { icon: string; onPress?: () => void }) {
  return (
    <Pressable accessibilityLabel={icon} onPress={onPress} style={styles.headerAction}>
      <MaterialCommunityIcons color={colors.primary} name={icon} size={26} />
    </Pressable>
  );
}
const vehicleImages = { car: carImage, bike: bikeImage, auto: autoImage };
function SavedPlaceCard({ place, onPress }: { place?: SavedPlace; onPress: () => void }) {
  const icon = place?.label === 'Work' ? 'briefcase' : 'home';
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.savedPlace}>
      <View style={styles.placeIcon}>
        <MaterialCommunityIcons color={colors.primary} name={icon} size={25} />
      </View>
      <View style={styles.savedPlaceCopy}>
        <DsText variant="bodyMedium">{place?.label ?? 'Add place'}</DsText>
        <DsText color={colors.textTertiary} numberOfLines={2} variant="caption">
          {place?.formatted_address ?? 'Choose address'}
        </DsText>
      </View>
      <MaterialCommunityIcons color={colors.primary} name="pencil-outline" size={18} />
    </Pressable>
  );
}
function SectionTitle({ title, action, onAction }: { title: string; action: string; onAction?: () => void }) {
  return (
    <View style={styles.sectionTitle}>
      <DsText variant="h1">{title}</DsText>
      {action ? <Pressable accessibilityRole="button" onPress={onAction}><DsText color={colors.primary}>{action}</DsText></Pressable> : null}
    </View>
  );
}
function RecentRide({ ride }: { ride: RecentRide }) {
  const [active, setActive] = useState(false);
  const date = ride.completed_at
    ? new Date(ride.completed_at).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Recently';
  const time = ride.final_duration_seconds
    ? `${Math.round(ride.final_duration_seconds / 60)} min`
    : '—';
  return (
    <Pressable
      accessibilityRole="button"
      onHoverIn={() => setActive(true)}
      onHoverOut={() => setActive(false)}
      onPressIn={() => setActive(true)}
      onPressOut={() => setActive(false)}
      style={[styles.recentPressable, active && styles.recentActive]}
    >
      <DsCard style={styles.recentRide}>
        <View style={styles.routeIcon}>
          <MaterialCommunityIcons color={colors.primary} name="map-marker" size={26} />
        </View>
        <View style={styles.rideInfo}>
          <DsText numberOfLines={1} variant="bodyMedium">
            {ride.pickup_address} → {ride.destination_address}
          </DsText>
          <DsText color={colors.textTertiary}>
            {date} • {time}
          </DsText>
        </View>
        <DsText color={colors.primary} variant="h2">
          ₹ {ride.fare_paise / 100}
        </DsText>
      </DsCard>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  avatar: { borderRadius: radius.pill, height: 54, width: 54 },
  content: {
    backgroundColor: colors.background,
    gap: spacing.xl,
    padding: spacing.xl,
    paddingBottom: spacing.massive,
  },
  greeting: { alignItems: 'center', flex: 1, flexDirection: 'row', gap: spacing.md },
  header: { alignItems: 'center', flexDirection: 'row', paddingTop: spacing.sm },
  headerAction: {
    ...shadows.card,
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: radius.md,
    borderWidth: 1,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  headerActions: { flexDirection: 'row', gap: spacing.md },
  name: { fontSize: 18, lineHeight: 34 },
  placeIcon: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  savedPlace: { alignItems: 'center', flex: 1, flexDirection: 'row', gap: spacing.sm },
  savedPlaceCopy: { flex: 1 },
  savedPlaces: { flexDirection: 'row', gap: spacing.sm, padding: spacing.md },
  rideRow: { flexDirection: 'row', gap: spacing.md },
  safetyCard: { alignItems: 'center', flexDirection: 'row', gap: spacing.md, padding: spacing.md },
  activeRide: { alignItems: 'center', backgroundColor: colors.primarySoft, borderColor: colors.primary, borderWidth: 1, flexDirection: 'row', gap: spacing.md, padding: spacing.md },
  safetyCopy: { flex: 1, gap: spacing.xxs },
  safetyIcon: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    height: 52,
    justifyContent: 'center',
    width: 52,
  },
  sectionTitle: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: -spacing.sm,
  },
  recentList: { gap: spacing.md },
  recentPressable: { borderRadius: radius.md },
  recentActive: {
    ...shadows.raised,
    borderColor: colors.primary,
    borderRadius: radius.md,
    borderWidth: 1,
    shadowColor: colors.primaryShadow,
    shadowOpacity: 1,
  },
  recentRide: { alignItems: 'center', flexDirection: 'row', gap: spacing.md, padding: spacing.md },
  routeIcon: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  rideInfo: { flex: 1, gap: spacing.xxs },
  safeArea: { backgroundColor: colors.background, flex: 1 },
});
