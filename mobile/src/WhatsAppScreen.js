import React, {
  useState,
} from 'react';

import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import * as Clipboard from 'expo-clipboard';
import NotificationBanner from './NotificationBanner';

import {
  createConversation,
} from './conversations';

import {
  streamAIMessage,
} from './messages';

import {
  getAccessToken,
} from './storage';

export default function WhatsAppScreen({
  preferredLanguage,
  onBack,
}) {
  const [recipient, setRecipient] =
    useState('');

  const [messageText, setMessageText] =
    useState('');

  const [suggestedReply, setSuggestedReply] =
    useState('');

  const [loading, setLoading] =
    useState(false);

  const [copying, setCopying] =
    useState(false);

  const [error, setError] =
    useState('');
  const [notification, setNotification] = useState({
    visible: false,
    type: 'info',
    message: '',
  }); 

  const [recipientError, setRecipientError] =
    useState('');

  const [messageError, setMessageError] =
    useState('');

  const [generationStarted, setGenerationStarted] =
    useState(false);

  const activeLanguage =
    preferredLanguage?.trim() || 'en';

  const handleRecipientChange = (value) => {
    setRecipient(value);

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
  const showNotification = (
    message,
    type = 'info'
  ) => {
    setNotification({
        visible: true,
        type,
        message,
    });
  };
  
  const dismissNotification = () => {
    setNotification({
        visible: false,
        type: 'info',
        message: '',
    });
  };

  const handleMessageChange = (value) => {
    setMessageText(value);
    setMessageError('');
    setError('');

    if (generationStarted) {
      setSuggestedReply('');
      setGenerationStarted(false);
    }
  };

  const validateRecipient = () => {
    const normalizedRecipient =
      recipient.trim();

    if (!normalizedRecipient) {
      setRecipientError(
        'Please enter a WhatsApp recipient phone number.'
      );
      return false;
    }

    const digitsOnly =
      normalizedRecipient.replace(
        /[\s\-().]/g,
        ''
      );

    if (
      !/^\+?[0-9]{7,15}$/.test(
        digitsOnly
      )
    ) {
      setRecipientError(
        'Please enter a valid phone number with country code.'
      );
      return false;
    }

    setRecipientError('');
    return true;
  };

  const validateMessage = () => {
    const normalizedMessage =
      messageText.trim();

    if (!normalizedMessage) {
      setMessageError(
        'Please enter a message.'
      );
      return false;
    }

    setMessageError('');
    return true;
  };

  const handleGenerateSuggestion =
    async () => {
      setError('');
      setSuggestedReply('');
      setGenerationStarted(true);

      const recipientValid =
        validateRecipient();

      const messageValid =
        validateMessage();

      if (
        !recipientValid ||
        !messageValid
      ) {
        setGenerationStarted(false);
        return;
      }

      try {
        setLoading(true);

        const token =
          await getAccessToken();

        if (!token) {
          throw new Error(
            'Your session has expired. Please log in again.'
          );
        }

        const conversation =
          await createConversation(
            token,
            `WhatsApp - ${recipient.trim()}`
          );

        if (
          !conversation ||
          !conversation.id
        ) {
          throw new Error(
            'Unable to create an AI conversation.'
          );
        }

        let generatedReply = '';

        await streamAIMessage(
          token,
          conversation.id,
          messageText.trim(),
          activeLanguage,
          (chunk) => {
            generatedReply += chunk;

            setSuggestedReply(
              (current) =>
                current + chunk
            );
          }
        );

        generatedReply =
          generatedReply.trim();

        if (!generatedReply) {
          throw new Error(
            'The AI returned an empty response. Please try again.'
          );
        }

        setSuggestedReply(
          generatedReply
        );

        showNotification(
            'AI reply generated successfully.',
            'success'
        );
      } catch (error) {
        setSuggestedReply('');

        setError(
          error?.message ||
            'Unable to generate an AI reply. Please try again.'
        );

        showNotification(
          error?.message ||
            'Unable to generate an AI reply. Please try again.',
          'error'
        );
      } finally {
        setLoading(false);
        setGenerationStarted(false);
      }
    };

  const handleUseSuggestion = () => {
    const suggestion =
      suggestedReply.trim();

    if (!suggestion) {
      return;
    }

    setMessageText(suggestion);
    setMessageError('');
    setError('');
  };

  const handleCopySuggestion =
    async () => {
      const suggestion =
        suggestedReply.trim();

      if (!suggestion) {
        return;
      }

      try {
        setCopying(true);

        await Clipboard.setStringAsync(
          suggestion
        );

        setError('');
      } catch (error) {
        setError(
          'Unable to copy the AI suggestion. Please try again.'
        );
      } finally {
        setCopying(false);
      }
    };

  const renderSuggestionState = () => {
    if (
      loading &&
      !suggestedReply
    ) {
      return (
        <View
          style={
            styles.suggestionLoading
          }
        >
          <ActivityIndicator
            size="small"
            color="#2563eb"
          />

          <Text
            style={
              styles.loadingSuggestionText
            }
          >
            Generating AI reply...
          </Text>
        </View>
      );
    }

    if (
      loading &&
      suggestedReply
    ) {
      return (
        <>
          <View
            style={
              styles.suggestionContainer
            }
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
            style={
              styles.streamingContainer
            }
          >
            <ActivityIndicator
              size="small"
              color="#2563eb"
            />

            <Text
              style={
                styles.streamingText
              }
            >
              Receiving AI response...
            </Text>
          </View>
        </>
      );
    }

    if (suggestedReply) {
      return (
        <>
          <View
            style={
              styles.suggestionContainer
            }
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
            <Pressable
              style={
                styles.secondaryButton
              }
              onPress={
                handleUseSuggestion
              }
              disabled={copying}
            >
              <Text
                style={
                  styles.secondaryButtonText
                }
              >
                Use Suggestion
              </Text>
            </Pressable>

            <Pressable
              style={
                styles.secondaryButton
              }
              onPress={
                handleCopySuggestion
              }
              disabled={copying}
            >
              <Text
                style={
                  styles.secondaryButtonText
                }
              >
                {copying
                  ? 'Copying...'
                  : 'Copy'}
              </Text>
            </Pressable>
          </View>
        </>
      );
    }

    if (
      generationStarted &&
      error
    ) {
      return (
        <View
          style={
            styles.generationErrorContainer
          }
        >
          <Text
            style={
              styles.generationErrorTitle
            }
          >
            Unable to generate a reply
          </Text>

          <Text
            style={
              styles.generationErrorText
            }
          >
            Check the error above and try
            generating the suggestion again.
          </Text>
        </View>
      );
    }

    return (
      <View
        style={
          styles.emptySuggestionContainer
        }
      >
        <Text
          style={
            styles.emptySuggestionTitle
          }
        >
          No AI suggestion yet
        </Text>

        <Text
          style={
            styles.emptySuggestion
          }
        >
          Enter a message and select
          Generate AI Reply to create a
          suggested response.
        </Text>
      </View>
    );
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
      <NotificationBanner
        visible={notification.visible} 
        type={notification.type}
        message={notification.message}
        onDismiss={dismissNotification}
      />

      <View style={styles.header}>
        <Pressable
          style={styles.backButton}
          onPress={onBack}
          disabled={loading}
        >
          <Text
            style={styles.backButtonText}
          >
            Back
          </Text>
        </Pressable>

        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>
            WhatsApp Assistant
          </Text>

          <Text
            style={styles.headerSubtitle}
          >
            Prepare WhatsApp messages with AI
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={
          styles.scrollContent
        }
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {error ? (
          <View
            style={styles.errorContainer}
          >
            <Text
              style={styles.errorText}
            >
              {error}
            </Text>
          </View>
        ) : null}

        <View style={styles.content}>
          <View style={styles.card}>
            <Text
              style={styles.sectionTitle}
            >
              Recipient
            </Text>

            <Text style={styles.label}>
              Phone number
            </Text>

            <TextInput
              style={[
                styles.input,
                recipientError &&
                  styles.inputError,
              ]}
              value={recipient}
              onChangeText={
                handleRecipientChange
              }
              placeholder="+91 9876543210"
              keyboardType="phone-pad"
              editable={!loading}
              autoCapitalize="none"
            />

            {recipientError ? (
              <Text
                style={
                  styles.fieldErrorText
                }
              >
                {recipientError}
              </Text>
            ) : null}

            <Text
              style={styles.helperText}
            >
              Enter the WhatsApp recipient's
              phone number, including the
              country code.
            </Text>
          </View>

          <View style={styles.card}>
            <View
              style={styles.messageHeader}
            >
              <Text
                style={styles.sectionTitle}
              >
                Message
              </Text>

              <Text
                style={styles.characterCounter}
              >
                {messageText.length}/2000
              </Text>
            </View>

            <TextInput
              style={[
                styles.messageInput,
                messageError &&
                  styles.messageInputError,
              ]}
              value={messageText}
              onChangeText={
                handleMessageChange
              }
              placeholder="Type your WhatsApp message..."
              placeholderTextColor="#9ca3af"
              multiline
              maxLength={2000}
              editable={!loading}
              textAlignVertical="top"
            />

            {messageError ? (
              <Text
                style={
                  styles.fieldErrorText
                }
              >
                {messageError}
              </Text>
            ) : (
              <Text
                style={
                  styles.messageHelperText
                }
              >
                Write the message you want to
                send or use as context for an
                AI-generated reply.
              </Text>
            )}
          </View>

          <View style={styles.card}>
            <Text
              style={styles.sectionTitle}
            >
              Reply Language
            </Text>

            <View
              style={
                styles.languageContainer
              }
            >
              <View
                style={
                  styles.languageInfo
                }
              >
                <Text
                  style={
                    styles.languageLabel
                  }
                >
                  AI response language
                </Text>

                <Text
                  style={
                    styles.languageValue
                  }
                >
                  {activeLanguage}
                </Text>
              </View>
            </View>

            <Text
              style={
                styles.languageDescription
              }
            >
              AI-generated replies will use your
              selected communication language.
              Change your preferred language from
              your profile settings.
            </Text>
          </View>

          <View style={styles.card}>
            <View
              style={styles.messageHeader}
            >
              <Text
                style={styles.sectionTitle}
              >
                AI Suggested Reply
              </Text>

              <Text
                style={styles.languageBadge}
              >
                {activeLanguage}
              </Text>
            </View>

            {renderSuggestionState()}

            <Text
              style={styles.languageHint}
            >
              Generated in {activeLanguage}
            </Text>
          </View>

          <Pressable
            style={[
              styles.primaryButton,
              loading &&
                styles.primaryButtonDisabled,
            ]}
            disabled={loading}
            onPress={
              handleGenerateSuggestion
            }
          >
            {loading ? (
              <View
                style={
                  styles.loadingContent
                }
              >
                <ActivityIndicator
                  size="small"
                  color="#ffffff"
                />

                <Text
                  style={[
                    styles.primaryButtonText,
                    styles.loadingText,
                  ]}
                >
                  Generating...
                </Text>
              </View>
            ) : (
              <Text
                style={
                  styles.primaryButtonText
                }
              >
                Generate AI Reply
              </Text>
            )}
          </Pressable>

          <Text
            style={styles.disclaimerText}
          >
            This step generates an AI suggestion.
            WhatsApp sending is not connected yet.
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#dddddd',
  },

  backButton: {
    paddingVertical: 6,
    paddingRight: 12,
  },

  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },

  headerContent: {
    flex: 1,
  },

  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },

  headerSubtitle: {
    marginTop: 3,
    fontSize: 12,
    color: '#6b7280',
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    paddingBottom: 32,
  },

  content: {
    padding: 16,
  },

  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },

  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 14,
  },

  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },

  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 14,
    fontSize: 16,
    backgroundColor: '#ffffff',
    color: '#111827',
  },

  inputError: {
    borderColor: '#dc2626',
  },

  fieldErrorText: {
    marginTop: 6,
    fontSize: 12,
    color: '#dc2626',
  },

  helperText: {
    marginTop: 7,
    fontSize: 12,
    lineHeight: 18,
    color: '#6b7280',
  },

  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  messageInput: {
    minHeight: 130,
    maxHeight: 220,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingTop: 12,
    paddingBottom: 12,
    fontSize: 16,
    lineHeight: 22,
    backgroundColor: '#ffffff',
    color: '#111827',
  },

  messageInputError: {
    borderColor: '#dc2626',
  },

  characterCounter: {
    marginBottom: 14,
    fontSize: 12,
    color: '#6b7280',
  },

  messageHelperText: {
    marginTop: 7,
    fontSize: 12,
    lineHeight: 18,
    color: '#6b7280',
  },

  languageContainer: {
    borderWidth: 1,
    borderColor: '#dbeafe',
    borderRadius: 12,
    backgroundColor: '#eff6ff',
    padding: 14,
  },

  languageInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  languageLabel: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '600',
  },

  languageValue: {
    fontSize: 15,
    color: '#2563eb',
    fontWeight: '700',
    textTransform: 'uppercase',
  },

  languageDescription: {
    marginTop: 9,
    fontSize: 12,
    lineHeight: 18,
    color: '#6b7280',
  },

  languageBadge: {
    marginBottom: 14,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: '#eff6ff',
    color: '#2563eb',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },

  suggestionLoading: {
    minHeight: 70,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  loadingSuggestionText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#374151',
  },

  streamingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },

  streamingText: {
    marginLeft: 7,
    fontSize: 12,
    color: '#2563eb',
  },

  suggestionContainer: {
    minHeight: 90,
    borderWidth: 1,
    borderColor: '#dbeafe',
    borderRadius: 12,
    padding: 14,
    backgroundColor: '#eff6ff',
  },

  suggestionText: {
    fontSize: 15,
    lineHeight: 23,
    color: '#111827',
  },

  emptySuggestionContainer: {
    minHeight: 90,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 10,
  },

  emptySuggestionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#374151',
    marginBottom: 6,
  },

  emptySuggestion: {
    textAlign: 'center',
    color: '#6b7280',
    fontSize: 13,
    lineHeight: 19,
  },

  generationErrorContainer: {
    minHeight: 90,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 10,
  },

  generationErrorTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#b00020',
    marginBottom: 6,
  },

  generationErrorText: {
    textAlign: 'center',
    color: '#6b7280',
    fontSize: 13,
    lineHeight: 19,
  },

  languageHint: {
    marginTop: 12,
    fontSize: 12,
    color: '#6b7280',
  },

  actionRow: {
    flexDirection: 'row',
    marginTop: 12,
  },

  secondaryButton: {
    flex: 1,
    minHeight: 44,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 10,
    marginRight: 8,
    backgroundColor: '#ffffff',
  },

  secondaryButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
  },

  primaryButton: {
    minHeight: 50,
    borderRadius: 12,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
  },

  primaryButtonDisabled: {
    opacity: 0.5,
  },

  primaryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },

  loadingContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  loadingText: {
    marginLeft: 8,
  },

  errorContainer: {
    padding: 12,
    backgroundColor: '#ffecec',
    borderBottomWidth: 1,
    borderBottomColor: '#ffcccc',
  },

  errorText: {
    color: '#b00020',
    fontSize: 13,
  },

  disclaimerText: {
    marginTop: 10,
    marginBottom: 8,
    textAlign: 'center',
    fontSize: 11,
    lineHeight: 16,
    color: '#6b7280',
  },
});