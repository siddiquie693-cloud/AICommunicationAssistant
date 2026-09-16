import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { getCurrentUser, logout } from './auth';
import {
  createConversation,
  getConversations,
} from './conversations';
import ConversationScreen from './ConversationScreen';
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from './storage';

export default function HomeScreen({ onLogout }) {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [conversationTitle, setConversationTitle] =
    useState('');
  const [selectedConversation, setSelectedConversation] =
    useState(null);
  const [creatingConversation, setCreatingConversation] =
    useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadConversations = async (token) => {
    const conversationData =
      await getConversations(token);

    setConversations(
      conversationData.results ||
      conversationData
    );
  };

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const token = await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        const data = await getCurrentUser(token);

        setUser(data);

        await loadConversations(token);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadCurrentUser();
  }, []);

  const handleCreateConversation = async () => {
    if (!conversationTitle.trim()) {
      Alert.alert(
        'Title required',
        'Please enter a conversation title.'
      );
      return;
    }

    try {
      setCreatingConversation(true);

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await createConversation(
        token,
        conversationTitle.trim()
      );

      setConversationTitle('');

      await loadConversations(token);

      Alert.alert(
        'Conversation created',
        'Your new conversation has been created.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to create conversation',
        err.message
      );
    } finally {
      setCreatingConversation(false);
    }
  };

  const handleLogout = async () => {
    try {
      const accessToken = await getAccessToken();
      const refreshToken = await getRefreshToken();

      if (accessToken && refreshToken) {
        await logout(
          accessToken,
          refreshToken
        );
      }
    } catch (err) {
      Alert.alert(
        'Logout error',
        err.message
      );
    } finally {
      await clearTokens();
      onLogout();
    }
  };

  if (selectedConversation) {
    return (
      <ConversationScreen
        conversation={selectedConversation}
        onBack={() => setSelectedConversation(null)}
      />
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />

        <Text style={styles.loadingText}>
          Loading your profile...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorTitle}>
          Unable to load profile
        </Text>

        <Text style={styles.errorText}>
          {error}
        </Text>

        <Pressable
          style={styles.logoutButton}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>
            Sign Out
          </Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>
        AI Communication Assistant
      </Text>

      <Text style={styles.subtitle}>
        Welcome back!
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Your profile
        </Text>

        <Text style={styles.cardText}>
          Username: {user?.username || 'N/A'}
        </Text>

        <Text style={styles.cardText}>
          Email: {user?.email || 'N/A'}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          New conversation
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Enter conversation title"
          value={conversationTitle}
          onChangeText={setConversationTitle}
          autoCapitalize="sentences"
          editable={!creatingConversation}
        />

        <Pressable
          style={[
            styles.createButton,
            creatingConversation &&
              styles.buttonDisabled,
          ]}
          onPress={handleCreateConversation}
          disabled={creatingConversation}
        >
          <Text style={styles.createButtonText}>
            {creatingConversation
              ? 'Creating...'
              : 'New Conversation'}
          </Text>
        </Pressable>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Your conversations
        </Text>

        {conversations.length === 0 ? (
          <Text style={styles.cardText}>
            No conversations yet.
          </Text>
        ) : (
          conversations.map((conversation) => (
            <Pressable
              key={conversation.id}
              style={styles.conversationItem}
              onPress={() =>
                setSelectedConversation(
                  conversation
                )
              }
            >
              <Text style={styles.conversationTitle}>
                {conversation.title}
              </Text>

              <Text style={styles.conversationDate}>
                {conversation.created_at}
              </Text>
            </Pressable>
          ))
        )}
      </View>

      <Pressable
        style={styles.logoutButton}
        onPress={handleLogout}
      >
        <Text style={styles.logoutButtonText}>
          Sign Out
        </Text>
      </Pressable>
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

  center: {
    flex: 1,
    backgroundColor: '#f5f7fb',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
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
    marginBottom: 16,
  },

  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },

  cardText: {
    fontSize: 15,
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
    backgroundColor: '#ffffff',
    marginBottom: 12,
  },

  createButton: {
    backgroundColor: '#111827',
    borderRadius: 12,
    paddingVertical: 16,
  },

  createButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },

  buttonDisabled: {
    opacity: 0.6,
  },

  conversationItem: {
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingVertical: 14,
  },

  conversationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },

  conversationDate: {
    fontSize: 13,
    color: '#6b7280',
  },

  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: '#6b7280',
  },

  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },

  errorText: {
    fontSize: 15,
    color: '#dc2626',
    textAlign: 'center',
  },

  logoutButton: {
    backgroundColor: '#dc2626',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 4,
  },

  logoutButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});
