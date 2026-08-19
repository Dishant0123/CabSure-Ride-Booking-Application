import AsyncStorage from '@react-native-async-storage/async-storage';
import auth, { type FirebaseAuthTypes } from '@react-native-firebase/auth';

import { apiClient, DRIVER_SESSION_KEY } from '../../../services/apiClient';

export type DriverProfile = { id: number; full_name: string; phone_number: string; status: string; operating_city: string | null; onboarding_completed: boolean };
export type DriverSession = { access_token: string; refresh_token: string; token_type: 'bearer'; driver: DriverProfile };
export type DriverAuthIntent = 'login' | 'signup';
export type DriverRegistrationIdentity = { idToken: string; fullName: string; phoneNumber: string };
export type DriverRegistrationPayload = { operating_city: string; registration_number: string; vehicle_make: string; vehicle_model: string; vehicle_year: number; vehicle_color?: string; vehicle_category: 'car' | 'bike' | 'auto'; seat_count: number; documents: { document_type: 'driving_licence' | 'vehicle_registration' | 'aadhaar' | 'vehicle_insurance'; document_number: string; storage_key: string }[] };

const OTP_REQUEST_TIMEOUT_MS = 30_000;

// Enables deterministic fictional-number testing on Android emulators without
// weakening verification in release builds or for production users.
if (__DEV__) {
  auth().settings.appVerificationDisabledForTesting = true;
}

function withTimeout<T>(operation: Promise<T>, code = 'auth/otp-request-timeout', message = 'OTP request timed out. Check your network and try again.'): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Object.assign(new Error(message), { code })), OTP_REQUEST_TIMEOUT_MS);
    operation.then(value => { clearTimeout(timeout); resolve(value); }, error => { clearTimeout(timeout); reject(error); });
  });
}

function isDriverSession(value: unknown): value is DriverSession {
  if (typeof value !== 'object' || value === null) return false;
  const session = value as Partial<DriverSession>;
  return typeof session.access_token === 'string' && typeof session.refresh_token === 'string' && typeof session.driver === 'object' && session.driver !== null;
}

async function saveSession(session: DriverSession): Promise<DriverSession> {
  await AsyncStorage.setItem(DRIVER_SESSION_KEY, JSON.stringify(session));
  return session;
}

/** Driver-only Firebase and CabSure session boundary. Login and signup use deliberately different API contracts. */
export const driverAuthService = {
  async resetPhoneChallenge(): Promise<void> {
    // Firebase may retain an incomplete phone-auth challenge after changing a number.
    // Signing out is safe when no user exists and guarantees the next OTP is a fresh challenge.
    if (auth().currentUser) await auth().signOut();
  },

  async requestOtp(phoneNumber: string): Promise<FirebaseAuthTypes.ConfirmationResult> {
    if (auth().currentUser) {
      await withTimeout(auth().signOut(), 'auth/session-reset-timeout', 'Previous phone session could not be reset.');
    }
    return withTimeout(auth().signInWithPhoneNumber(`+91${phoneNumber}`));
  },

  async verifyOtp(confirmation: FirebaseAuthTypes.ConfirmationResult, otp: string, intent: DriverAuthIntent, fullName?: string): Promise<DriverSession> {
    const firebaseUser = await withTimeout(confirmation.confirm(otp), 'auth/otp-verification-timeout', 'OTP verification timed out.');
    const firebaseAccount = firebaseUser?.user;
    if (!firebaseAccount) throw new Error('Firebase did not return an authenticated Driver.');
    const idToken = await withTimeout(firebaseAccount.getIdToken(true), 'auth/token-timeout', 'Secure sign-in token timed out.');
    if (!idToken) throw new Error('Unable to create a secure Driver verification token. Please request a new OTP.');
    const payload = intent === 'signup' ? { id_token: idToken, full_name: fullName?.trim() ?? '' } : { id_token: idToken };
    try {
      const response = await apiClient.post<DriverSession>(`/api/v1/auth/drivers/firebase/${intent}`, payload);
      return saveSession(response.data);
    } catch (error) {
      await auth().signOut();
      throw error;
    }
  },

  async verifySignupPhone(confirmation: FirebaseAuthTypes.ConfirmationResult, otp: string, fullName: string): Promise<DriverRegistrationIdentity> {
    const firebaseUser = await withTimeout(confirmation.confirm(otp), 'auth/otp-verification-timeout', 'OTP verification timed out.');
    const firebaseAccount = firebaseUser?.user;
    if (!firebaseAccount) throw new Error('Firebase did not return an authenticated Driver.');
    const idToken = await withTimeout(firebaseAccount.getIdToken(true), 'auth/token-timeout', 'Secure sign-in token timed out.');
    const phoneNumber = firebaseAccount.phoneNumber;
    if (!idToken || !phoneNumber) throw new Error('Unable to verify this mobile number. Please request a new OTP.');
    return { idToken, fullName: fullName.trim(), phoneNumber };
  },

  async getSession(): Promise<DriverSession | null> {
    const value = await AsyncStorage.getItem(DRIVER_SESSION_KEY);
    if (!value) return null;
    try {
      const session: unknown = JSON.parse(value);
      if (isDriverSession(session)) return session;
    } catch { /* Remove malformed persisted data below. */ }
    await AsyncStorage.removeItem(DRIVER_SESSION_KEY);
    return null;
  },

  async refreshSession(): Promise<DriverSession | null> {
    const session = await this.getSession();
    if (!session) return null;
    try {
      const response = await apiClient.post<DriverSession>('/api/v1/auth/drivers/refresh', { refresh_token: session.refresh_token });
      return saveSession(response.data);
    } catch {
      await this.clearSession();
      return null;
    }
  },

  async completeRegistration(identity: DriverRegistrationIdentity, payload: DriverRegistrationPayload): Promise<DriverSession> {
    const response = await apiClient.post<DriverSession>('/api/v1/auth/drivers/firebase/register', { id_token: identity.idToken, full_name: identity.fullName, ...payload });
    return saveSession(response.data);
  },

  async completeOnboarding(payload: { operating_city: string; registration_number: string; vehicle_make: string; vehicle_model: string; vehicle_year: number; vehicle_color?: string; vehicle_category: 'car' | 'bike' | 'auto'; seat_count: number }): Promise<DriverSession> {
    const response = await apiClient.post<DriverProfile>('/api/v1/auth/drivers/onboarding', payload);
    const session = await this.getSession();
    if (!session) throw new Error('Your Driver session has expired. Please sign in again.');
    return saveSession({ ...session, driver: response.data });
  },

  async clearSession(): Promise<void> {
    await AsyncStorage.removeItem(DRIVER_SESSION_KEY);
    if (auth().currentUser) await auth().signOut();
  },
};
