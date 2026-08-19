export const colors = {
  primary: '#2563EB',
  primaryPressed: '#1F54D4',
  primarySoft: '#EEF3FF',
  primaryShadow: 'rgba(37, 99, 235, 0.20)',
  background: '#F8FAFF',
  surface: '#FFFFFF',
  surfaceMuted: '#F5F7FB',
  textPrimary: '#172033',
  textSecondary: '#697386',
  textTertiary: '#98A2B3',
  border: '#E5EAF2',
  borderStrong: '#C9D3E2',
  success: '#20A86B',
  successSoft: '#EAF8F1',
  warning: '#E5A320',
  warningSoft: '#FFF7E5',
  error: '#E05252',
  errorSoft: '#FDEEEE',
  overlay: 'rgba(23, 32, 51, 0.48)',
  transparent: 'transparent',
  white: '#FFFFFF',
  black: '#000000',
  // Compatibility aliases used by the first Driver screens.
  text: '#172033',
  danger: '#E05252',
  dangerSoft: '#FDEEEE',
} as const;

export const spacing = { xxs: 2, xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24, xxxl: 32, huge: 40, massive: 48 } as const;
export const radius = { none: 0, xs: 4, sm: 8, md: 12, lg: 16, xl: 20, pill: 999 } as const;
export const typography = {
  family: { regular: 'Poppins-Regular', medium: 'Poppins-Medium', semibold: 'Poppins-SemiBold', bold: 'Poppins-Bold' },
  display: { fontSize: 32, lineHeight: 42, fontFamily: 'Poppins-Bold' },
  h1: { fontSize: 24, lineHeight: 32, fontFamily: 'Poppins-SemiBold' },
  h2: { fontSize: 20, lineHeight: 28, fontFamily: 'Poppins-SemiBold' },
  h3: { fontSize: 18, lineHeight: 26, fontFamily: 'Poppins-SemiBold' },
  body: { fontSize: 14, lineHeight: 22, fontFamily: 'Poppins-Regular' },
  bodyMedium: { fontSize: 14, lineHeight: 22, fontFamily: 'Poppins-Medium' },
  label: { fontSize: 14, lineHeight: 20, fontFamily: 'Poppins-Medium' },
  caption: { fontSize: 12, lineHeight: 18, fontFamily: 'Poppins-Regular' },
} as const;
export const shadows = {
  card: { elevation: 2, shadowColor: colors.black, shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 6 },
  raised: { elevation: 4, shadowColor: colors.black, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 10 },
  floating: { elevation: 8, shadowColor: colors.black, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.14, shadowRadius: 18 },
} as const;
