import AsyncStorage from '@react-native-async-storage/async-storage';
import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';

import { apiClient } from '../../../services/apiClient';

const SESSION_KEY = '@cabapp/passenger-session';
const PROFILE_NAME_KEY = '@cabapp/passenger-profile-name';

export type AuthSession = { access_token: string; refresh_token: string; token_type: 'bearer' };
export type PhoneAuthIntent = 'login' | 'signup';

export const authService = {
  async requestOtp(phoneNumber: string, intent: PhoneAuthIntent): Promise<FirebaseAuthTypes.ConfirmationResult> {
    if (intent === 'login') {
      await apiClient.post('/api/v1/auth/passengers/firebase/login/preflight', { phone_number: phoneNumber });
    }
    return auth().signInWithPhoneNumber(`+91${phoneNumber}`);
  },
  async verifyOtp(confirmation: FirebaseAuthTypes.ConfirmationResult, otp: string, intent: PhoneAuthIntent, fullName?: string): Promise<AuthSession> {
    const firebaseUser = await confirmation.confirm(otp);
    if (!firebaseUser || !firebaseUser.user) {
      throw new Error('Firebase did not return an authenticated user.');
    }
    const idToken = await firebaseUser.user.getIdToken();
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
