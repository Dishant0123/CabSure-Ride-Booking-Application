import { StyleSheet, View } from 'react-native';
import { DriverBrandLogo } from './DriverBrandLogo';

export function DriverBrandMark({ size = 60 }: { size?: number }) { return <View accessibilityLabel="CabSure Driver" style={[styles.box, { height: size, width: size }]}><DriverBrandLogo size={size * 2}/></View>; }
const styles = StyleSheet.create({ box: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' } });
