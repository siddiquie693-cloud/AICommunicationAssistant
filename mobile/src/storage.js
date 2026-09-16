import * as SecureStore from 'expo-secure-store';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export async function saveTokens(accessToken, refreshToken) {
  if (!accessToken || !refreshToken) {
    throw new Error('Access and refresh tokens are required.');
  }

  await SecureStore.setItemAsync(
    ACCESS_TOKEN_KEY,
    accessToken
  );

  await SecureStore.setItemAsync(
    REFRESH_TOKEN_KEY,
    refreshToken
  );
}

export async function getAccessToken() {
  return SecureStore.getItemAsync(
    ACCESS_TOKEN_KEY
  );
}

export async function getRefreshToken() {
  return SecureStore.getItemAsync(
    REFRESH_TOKEN_KEY
  );
}

export async function hasAccessToken() {
  const token = await getAccessToken();

  return Boolean(token);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(
    ACCESS_TOKEN_KEY
  );

  await SecureStore.deleteItemAsync(
    REFRESH_TOKEN_KEY
  );
}