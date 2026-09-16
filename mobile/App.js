import { StatusBar } from 'expo-status-bar';
import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useEffect, useState } from 'react';

import { login } from './src/auth';
import HomeScreen from './src/HomeScreen';
import {
  hasAccessToken,
  saveTokens,
} from './src/storage';

export default function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuthentication = async () => {
      const authenticated = await hasAccessToken();

      if (authenticated) {
        setIsAuthenticated(true);
      }
    };

    checkAuthentication();
  }, []);

  const handleLogin = async () => {
    if (!username.trim() || !password) {
      Alert.alert(
        'Login required',
        'Please enter your username and password.'
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
        error.message
      );
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) {
    return (
      <HomeScreen
        onLogout={() => setIsAuthenticated(false)}
      />
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />

      <Text style={styles.title}>
        AI Communication Assistant
      </Text>

      <Text style={styles.subtitle}>
        Sign in to continue
      </Text>

      <View style={styles.card}>
        <Text style={styles.label}>Username</Text>

        <TextInput
          style={styles.input}
          placeholder="Enter username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
        />

        <Text style={styles.label}>Password</Text>

        <TextInput
          style={styles.input}
          placeholder="Enter password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <Pressable
          style={[
            styles.button,
            loading && styles.buttonDisabled,
          ]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f7fb',
    paddingHorizontal: 24,
    paddingTop: 90,
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