import React, { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';

const PhoneCallScreen = ({
  preferredLanguage,
  onBack,
}) => {
  const [recipient, setRecipient] = useState('');
  const [recipientError, setRecipientError] =
    useState('');

  const [callStatus, setCallStatus] =
    useState('ready');

  const [suggestedReply, setSuggestedReply] =
    useState('');

  const [copying, setCopying] =
    useState(false);

  const [error, setError] =
    useState('');

  const activeLanguage =
    preferredLanguage?.trim() || 'en';

  const handleRecipientChange = (value) => {
    setRecipient(value);
    setError('');

    const normalized = value
      .trim()
      .replace(/[\s\-().]/g, '');

    if (!value.trim()) {
      setRecipientError('');
      return;
    }

    if (!/^\+?[0-9]{7,15}$/.test(normalized)) {
      setRecipientError(
        'Please enter a valid phone number with country code.'
      );
      return;
    }

    setRecipientError('');
  };

  const handleStartCall = () => {
    setError('');

    const normalized = recipient
      .trim()
      .replace(/[\s\-().]/g, '');

    if (!recipient.trim()) {
      setRecipientError(
        'Please enter a phone number.'
      );
      return;
    }

    if (
      !/^\+?[0-9]{7,15}$/.test(
        normalized
      )
    ) {
      setRecipientError(
        'Please enter a valid phone number with country code.'
      );
      return;
    }

    setRecipientError('');
    setCallStatus('connecting');

    setTimeout(() => {
      setCallStatus('ready');

      setError(
        'Phone calling is not connected yet.'
      );
    }, 1500);
  };

  const handleCopy = async () => {
    if (!suggestedReply.trim()) {
      return;
    }

    try {
      setCopying(true);

      await Clipboard.setStringAsync(
        suggestedReply
      );
    } catch (copyError) {
      setError(
        'Unable to copy the AI suggestion.'
      );
    } finally {
      setCopying(false);
    }
  };

  const getStatusText = () => {
    switch (callStatus) {
      case 'connecting':
        return 'Connecting...';

      case 'ready':
        return 'Ready to call';

      default:
        return 'Ready to call';
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={
        Platform.OS === 'ios'
          ? 'padding'
          : undefined
      }
    >
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={onBack}
        >
          <Text style={styles.backButtonText}>
            ←
          </Text>
        </TouchableOpacity>

        <Text style={styles.headerTitle}>
          Phone Call Assistant
        </Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={
          styles.scrollContent
        }
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          <Text style={styles.label}>
            Phone number
          </Text>

          <TextInput
            value={recipient}
            onChangeText={
              handleRecipientChange
            }
            placeholder="+91 9876543210"
            placeholderTextColor="#888"
            keyboardType="phone-pad"
            autoCapitalize="none"
            editable={
              callStatus !== 'connecting'
            }
            style={[
              styles.input,
              recipientError &&
                styles.inputError,
            ]}
          />

          {recipientError ? (
            <Text style={styles.errorText}>
              {recipientError}
            </Text>
          ) : null}
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>
            Communication language
          </Text>

          <View style={styles.languageBox}>
            <Text style={styles.languageLabel}>
              AI response language
            </Text>

            <Text style={styles.languageText}>
              {activeLanguage}
            </Text>
          </View>

          <Text style={styles.helperText}>
            AI-generated call suggestions
            will use your preferred language.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>
            Call status
          </Text>

          <View style={styles.statusRow}>
            {callStatus === 'connecting' ? (
              <ActivityIndicator
                size="small"
              />
            ) : null}

            <Text style={styles.statusText}>
              {getStatusText()}
            </Text>
          </View>

          <TouchableOpacity
            style={[
              styles.startCallButton,
              callStatus === 'connecting' &&
                styles.disabledButton,
            ]}
            onPress={handleStartCall}
            disabled={
              callStatus === 'connecting'
            }
          >
            {callStatus === 'connecting' ? (
              <ActivityIndicator
                size="small"
              />
            ) : (
              <Text
                style={
                  styles.startCallButtonText
                }
              >
                Start Call
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {error ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>
              {error}
            </Text>
          </View>
        ) : null}

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>
            AI Suggested Response
          </Text>

          {suggestedReply ? (
            <>
              <View
                style={styles.suggestionBox}
              >
                <Text
                  style={
                    styles.suggestionText
                  }
                >
                  {suggestedReply}
                </Text>
              </View>

              <View
                style={styles.actionRow}
              >
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={handleCopy}
                  disabled={copying}
                >
                  {copying ? (
                    <ActivityIndicator
                      size="small"
                    />
                  ) : (
                    <Text
                      style={
                        styles.actionButtonText
                      }
                    >
                      Copy
                    </Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    setError('');
                  }}
                >
                  <Text
                    style={
                      styles.actionButtonText
                    }
                  >
                    Use Suggestion
                  </Text>
                </TouchableOpacity>
              </View>
            </>
          ) : (
            <View style={styles.emptyState}>
              <Text
                style={styles.emptyStateText}
              >
                AI-generated response
                suggestions will appear here
                when speech and call AI
                integration is connected.
              </Text>
            </View>
          )}
        </View>

        <View style={styles.comingSoonCard}>
          <Text
            style={styles.comingSoonTitle}
          >
            Phone calling
          </Text>

          <Text
            style={styles.comingSoonText}
          >
            Phone calling integration is
            coming later. This screen currently
            provides the communication UI only.
          </Text>
        </View>

        <TouchableOpacity
          style={styles.backBottomButton}
          onPress={onBack}
        >
          <Text
            style={styles.backBottomButtonText}
          >
            ← Back
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },

  header: {
    minHeight: 60,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    backgroundColor: '#fff',
  },

  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },

  backButtonText: {
    fontSize: 28,
  },

  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '700',
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },

  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e2e2',
  },

  label: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 8,
  },

  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },

  inputError: {
    borderColor: '#d93025',
  },

  errorText: {
    marginTop: 8,
    fontSize: 13,
    lineHeight: 18,
    color: '#d93025',
  },

  languageBox: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#fafafa',
  },

  languageLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },

  languageText: {
    fontSize: 16,
    fontWeight: '600',
  },

  helperText: {
    marginTop: 8,
    fontSize: 13,
    lineHeight: 18,
    color: '#666',
  },

  statusRow: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },

  statusText: {
    fontSize: 15,
    fontWeight: '600',
  },

  startCallButton: {
    minHeight: 46,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    backgroundColor: '#111',
  },

  startCallButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },

  disabledButton: {
    opacity: 0.6,
  },

  errorCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#f0c8c8',
  },

  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 12,
  },

  suggestionBox: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#fafafa',
  },

  suggestionText: {
    fontSize: 15,
    lineHeight: 22,
  },

  emptyState: {
    minHeight: 100,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
  },

  emptyStateText: {
    textAlign: 'center',
    fontSize: 14,
    lineHeight: 20,
    color: '#777',
  },

  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },

  actionButton: {
    flex: 1,
    minHeight: 44,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },

  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },

  comingSoonCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e2e2',
  },

  comingSoonTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
  },

  comingSoonText: {
    fontSize: 13,
    lineHeight: 19,
    color: '#666',
  },

  backBottomButton: {
    minHeight: 46,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },

  backBottomButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
});

export default PhoneCallScreen;
