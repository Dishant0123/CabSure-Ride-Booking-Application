import { StyleSheet, View } from 'react-native';
// import { colors } from '../../theme';
import { BrandLogo } from './BrandLogo';

type BrandMarkProps = { size?: number };

export function BrandMark({ size = 60 }: BrandMarkProps) {
  return (
    <View accessibilityLabel="CabSure" style={[styles.box, { height: size, width: size }]}>
      <BrandLogo size={size * 2} />
    </View>
  );
}
const styles = StyleSheet.create({
  box: {
    alignItems: 'center',
    // backgroundColor: colors.surface,
    // borderColor: colors.primarySoft,
    // borderRadius: 50,
    // borderWidth: 1,
    justifyContent: 'center',
    overflow: 'hidden',
  },
});
