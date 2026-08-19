import AsyncStorage from '@react-native-async-storage/async-storage';
import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';

import { apiClient } from '../../../services/apiClient';

const SESSION_KEY = '@cabapp/passenger-session';
const PROFILE_NAME_KEY = '@cabapp/passenger-profile-name';

// Firebase fictional phone numbers do not need Play Integrity/reCAPTCHA.
// Keep the bypass strictly inside Metro development builds; release builds
// always use Firebase's normal Android app verification.
if (__DEV__) {
  auth().settings.appVerificationDisabledForTesting = true;
}

export type AuthSession = { access_token: string; refresh_token: string; token_type: 'bearer' };
export type PhoneAuthIntent = 'login' | 'signup';

const FIREBASE_TIMEOUT_MS = 30_000;

function withFirebaseTimeout<T>(operation: Promise<T>, code: string, message: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(Object.assign(new Error(message), { code })),
      FIREBASE_TIMEOUT_MS,
    );
    operation.then(
      value => { clearTimeout(timer); resolve(value); },
      error => { clearTimeout(timer); reject(error); },
    );
  });
}

export const authService = {
  async requestOtp(phoneNumber: string, intent: PhoneAuthIntent): Promise<FirebaseAuthTypes.ConfirmationResult> {
    if (intent === 'login') {
      await apiClient.post('/api/v1/auth/passengers/firebase/login/preflight', { phone_number: phoneNumber });
    }
    // A Firebase user may survive an app or Metro restart. Starting a second
    // native phone challenge over that user can remain unresolved on Android.
    if (auth().currentUser) {
      await withFirebaseTimeout(
        auth().signOut(),
        'auth/session-reset-timeout',
        'Previous phone session could not be reset.',
      );
    }
    return withFirebaseTimeout(
      auth().signInWithPhoneNumber(`+91${phoneNumber}`),
      'auth/otp-request-timeout',
      'OTP request timed out.',
    );
  },
  async verifyOtp(confirmation: FirebaseAuthTypes.ConfirmationResult, otp: string, intent: PhoneAuthIntent, fullName?: string): Promise<AuthSession> {
    const firebaseUser = await withFirebaseTimeout(
      confirmation.confirm(otp),
      'auth/otp-verification-timeout',
      'OTP verification timed out.',
    );
    if (!firebaseUser || !firebaseUser.user) {
      throw new Error('Firebase did not return an authenticated user.');
    }
    const idToken = await withFirebaseTimeout(
      firebaseUser.user.getIdToken(true),
      'auth/token-timeout',
      'Secure sign-in token timed out.',
    );
    try {
      const route = intent === 'signup' ? '/api/v1/auth/passengers/firebase/signup' : '/api/v1/auth/passengers/firebase/login';
      const response = await apiClient.post<AuthSession>(route, { id_token: idToken, full_name: fullName });
      await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      await auth().signOut();
      throw error;
    }
  },
  async clearSession(): Promise<void> {
    await AsyncStorage.removeItem(SESSION_KEY);
    if (auth().currentUser) await auth().signOut();
  },
  async hasSession(): Promise<boolean> {
    const value = await AsyncStorage.getItem(SESSION_KEY);
    if (!value) return false;
    try { return Boolean((JSON.parse(value) as AuthSession).access_token); }
    catch { await AsyncStorage.removeItem(SESSION_KEY); return false; }
  },
  async saveProfileName(name: string): Promise<void> { await AsyncStorage.setItem(PROFILE_NAME_KEY, name.trim()); },
  async getProfileName(): Promise<string | null> { return AsyncStorage.getItem(PROFILE_NAME_KEY); },
};
