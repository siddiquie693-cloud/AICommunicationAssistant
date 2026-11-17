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

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from './src/theme';

import { login } from './src/auth';

import HomeScreen from './src/HomeScreen';

import NIRAPersonalProfileScreen from './src/NIRAPersonalProfileScreen';

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
  
  const [activeScreen, setActiveScreen] = useState('home');  

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
          {activeScreen === 'nira-profile' ? (
            <NIRAPersonalProfileScreen
              onBack={() => 
                setActiveScreen('home')
              }
            />
          ) : (
            <HomeScreen
              onLogout={() =>
                setIsAuthenticated(false)
              }
              onOpenNIRAPersonalProfile={() =>
                setActiveScreen('nira-profile')
              }
            />
          )}
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
        NIRA AI
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
          placeholderTextColor={COLORS.textSecondary}
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          autoCorrect={false}
          editable={!loading}
          accessibilityLabel="Username"
        />

        <Text style={styles.label}>
          Password
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Enter password"
          placeholderTextColor={COLORS.textSecondary}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          editable={!loading}
          accessibilityLabel="Password"
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
    backgroundColor: COLORS.background,
  },

  homeContainer: {
    flex: 1,
  },

  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: SPACING.xl,
    paddingTop: 60,
    justifyContent: 'center',
  },

  title: {
    fontSize: TYPOGRAPHY.display,
    fontWeight: '800',
    color: COLORS.primary,
    marginBottom: SPACING.sm,
  },

  subtitle: {
    fontSize: TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xxl + SPACING.sm,
  },

  card: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.xl,
    padding: SPACING.xl,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  label: {
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },

  input: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.lg,
    fontSize: TYPOGRAPHY.body,
    marginBottom: SPACING.xl,
    backgroundColor: COLORS.background,
    color: COLORS.text,
  },

  button: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    minHeight: 54,
    paddingVertical: SPACING.lg,
    marginTop: SPACING.xs,
    alignItems: 'center',
    justifyContent: 'center',
  },

  buttonDisabled: {
    opacity: 0.6,
  },

  buttonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
    textAlign: 'center',
  },
});

