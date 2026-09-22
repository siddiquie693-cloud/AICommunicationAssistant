import NetInfo from '@react-native-community/netinfo';

export async function getNetworkState() {
  return NetInfo.fetch();
}

export function subscribeToNetworkState(
  listener
) {
  return NetInfo.addEventListener(listener);
}

export async function isNetworkAvailable() {
  const state = await NetInfo.fetch();

  return Boolean(
    state.isConnected &&
    state.isInternetReachable !== false
  );
}