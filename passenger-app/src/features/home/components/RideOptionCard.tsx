import { useState } from 'react';
import { Animated, Pressable, StyleSheet, View, type ImageSourcePropType } from 'react-native';
import { DsCard, DsText } from '../../../components/design-system';
import { colors, spacing } from '../../../theme';
import { ImagePlaceholder } from './ImagePlaceholder';
type RideOptionCardProps = {
  name: string;
  eta: string;
  fare: string;
  imageSource?: ImageSourcePropType;
  selected?: boolean;
  onPress?: () => void;
};

export function RideOptionCard({
  name,
  eta,
  fare,
  imageSource,
  selected = false,
  onPress,
}: RideOptionCardProps) {
  const [lift] = useState(() => new Animated.Value(0));
  const animate = (value: number) =>
    Animated.spring(lift, {
      toValue: value,
      useNativeDriver: true,
      speed: 28,
      bounciness: 2,
    }).start();
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      onPressIn={() => animate(1)}
      onPressOut={() => animate(0)}
      style={styles.pressable}
    >
      <Animated.View
        style={[
          styles.animated,
          {
            transform: [
              { translateY: lift.interpolate({ inputRange: [0, 1], outputRange: [0, -4] }) },
            ],
          },
        ]}
      >
        <DsCard
          elevated
          style={[styles.card, selected && styles.selected, styles.interactionShadow]}
        >
          <ImagePlaceholder label={`${name} image`} source={imageSource} style={styles.image} />
          <View style={styles.details}>
            <DsText variant="h3">{name}</DsText>
            <DsText color={colors.textTertiary} variant="body">
              {eta}
            </DsText>
            {selected && (
              <DsText color={colors.primary} variant="body">
                Base fare: ₹ {fare}
              </DsText>
            )}
          </View>
        </DsCard>
      </Animated.View>
    </Pressable>
  );
}
const styles = StyleSheet.create({
  animated: { flex: 1 },
  card: { flex: 1, gap: spacing.sm, minWidth: 106, padding: spacing.md },
  details: { alignItems: 'center', gap: spacing.xxs },
  image: { height: 62, width: '100%' },
  interactionShadow: { shadowColor: colors.primaryShadow, shadowOpacity: 1, shadowRadius: 12 },
  pressable: { flex: 1 },
  selected: { borderColor: colors.primary, borderWidth: 1.5 },
});
