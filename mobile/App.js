import { StatusBar } from 'expo-status-bar';

import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  useEffect,
  useState,
} from 'react';

import { login } from './src/auth';

import HomeScreen from './src/HomeScreen';

import {
  hasAccessToken,
  saveTokens,
} from './src/storage';

import {
  setSessionExpiredHandler,
} from './src/session';

import {
  subscribeToNetworkState,
} from './src/network';

import NetworkStatusBanner from './src/NetworkStatusBanner';

export default function App() {
  const [username, setUsername] =
    useState('');

  const [password, setPassword] =
    useState('');

  const [loading, setLoading] =
    useState(false);

  const [isAuthenticated, setIsAuthenticated] =
    useState(false);

  const [isOffline, setIsOffline] =
    useState(false);

  useEffect(() => {
    let mounted = true;

    const checkAuthentication =
      async () => {
        try {
          const authenticated =
            await hasAccessToken();

          if (
            mounted &&
            authenticated
          ) {
            setIsAuthenticated(true);
          }
        } catch (error) {
          if (mounted) {
            setIsAuthenticated(false);
          }
        }
      };

    checkAuthentication();

    const unsubscribe =
      subscribeToNetworkState(
        (state) => {
          if (!mounted) {
            return;
          }

          const offline =
            !state.isConnected ||
            state.isInternetReachable ===
              false;

          setIsOffline(offline);
        }
      );

    setSessionExpiredHandler(() => {
      if (!mounted) {
        return;
      }

      setIsAuthenticated(false);

      Alert.alert(
        'Session expired',
        'Your session has expired. Please log in again.'
      );
    });

    return () => {
      mounted = false;

      unsubscribe();

      setSessionExpiredHandler(null);
    };
  }, []);

  const handleLogin = async () => {
    if (!username.trim() || !password) {
      Alert.alert(
        'Login required',
        'Please enter your username and password.'
      );

      return;
    }

    if (isOffline) {
      Alert.alert(
        'No internet connection',
        'Please check your network connection and try again.'
      );

      return;
    }

    try {
      setLoading(true);

      const data = await login(
        username.trim(),
        password
      );

      await saveTokens(
        data.access,
        data.refresh
      );

      Alert.alert(
        'Login successful',
        'Authentication completed successfully.'
      );

      setIsAuthenticated(true);
    } catch (error) {
      Alert.alert(
        'Login failed',
        error.message ||
          'Unable to sign in. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) {
    return (
      <View style={styles.authenticatedContainer}>
        <NetworkStatusBanner
          isOffline={isOffline}
        />

        <View style={styles.homeContainer}>
          <HomeScreen
            onLogout={() =>
              setIsAuthenticated(false)
            }
          />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />

      <NetworkStatusBanner
        isOffline={isOffline}
      />

      <Text style={styles.title}>
        AI Communication Assistant
      </Text>

      <Text style={styles.subtitle}>
        Sign in to continue
      </Text>

      <View style={styles.card}>
        <Text style={styles.label}>
          Username
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Enter username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          editable={!loading}
        />

        <Text style={styles.label}>
          Password
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Enter password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          editable={!loading}
        />

        <Pressable
          style={[
            styles.button,
            (loading || isOffline) &&
              styles.buttonDisabled,
          ]}
          onPress={handleLogin}
          disabled={
            loading || isOffline
          }
          accessibilityRole="button"
          accessibilityLabel="Sign in"
          accessibilityState={{
            disabled:
              loading || isOffline,
            busy: loading,
          }}
        >
          <Text style={styles.buttonText}>
            {loading
              ? 'Signing in...'
              : 'Sign In'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  authenticatedContainer: {
    flex: 1,
    backgroundColor: '#f5f7fb',
  },

  homeContainer: {
    flex: 1,
  },

  container: {
    flex: 1,
    backgroundColor: '#f5f7fb',
    paddingHorizontal: 24,
    paddingTop: 60,
  },

  title: {
    fontSize: 27,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },

  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },

  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 24,
  },

  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },

  input: {
    height: 52,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    marginBottom: 20,
    backgroundColor: '#ffffff',
  },

  button: {
    backgroundColor: '#111827',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 4,
  },

  buttonDisabled: {
    opacity: 0.6,
  },

  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});