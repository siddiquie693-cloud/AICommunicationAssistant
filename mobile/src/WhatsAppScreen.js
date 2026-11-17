
import React, { useState } from 'react';

import {
  View,
  Text,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  useWindowDimensions,
} from 'react-native';

import * as Clipboard from 'expo-clipboard';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from './theme';

import NIRAHeader from './components/NIRAHeader';
import NIRACard from './components/NIRACard';
import NIRAButton from './components/NIRAButton';
import NIRALoader from './components/NIRALoader';
import NIRABadge from './components/NIRABadge';
import NIRAEmptyState from './components/NIRAEmptyState';

import NotificationBanner from './NotificationBanner';

import { createConversation } from './conversations';
import { streamAIMessage } from './messages';
import { getAccessToken } from './storage';

export default function WhatsAppScreen({
  preferredLanguage,
  onBack,
}) {
  const { width } = useWindowDimensions();

  const horizontalPadding =
    width < 360 ? 12 : width < 600 ? 16 : 24;

  const contentMaxWidth =
    width >= 900 ? 760 : undefined;

  const [recipient, setRecipient] = useState('');
  const [messageText, setMessageText] = useState('');
  const [suggestedReply, setSuggestedReply] = useState('');

  const [loading, setLoading] = useState(false);
  const [copying, setCopying] = useState(false);

  const [error, setError] = useState('');
  const [recipientError, setRecipientError] = useState('');
  const [messageError, setMessageError] = useState('');

  const [generationStarted, setGenerationStarted] =
    useState(false);

  const [notification, setNotification] = useState({
    visible: false,
    type: 'info',
    message: '',
  });

  const activeLanguage =
    preferredLanguage?.trim() || 'en';

  // --------------------------------
  // Notification handling
  // --------------------------------

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

  // --------------------------------
  // Recipient validation
  // --------------------------------

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

  const validateRecipient = () => {
    const normalizedRecipient = recipient.trim();

    if (!normalizedRecipient) {
      setRecipientError(
        'Please enter a WhatsApp recipient phone number.'
      );
      return false;
    }

    const digitsOnly = normalizedRecipient.replace(
      /[\s\-().]/g,
      ''
    );

    if (!/^\+?[0-9]{7,15}$/.test(digitsOnly)) {
      setRecipientError(
        'Please enter a valid phone number with country code.'
      );
      return false;
    }

    setRecipientError('');
    return true;
  };

  // --------------------------------
  // Message handling
  // --------------------------------

  const handleMessageChange = (value) => {
    setMessageText(value);
    setMessageError('');
    setError('');

    if (generationStarted) {
      setSuggestedReply('');
      setGenerationStarted(false);
    }
  };

  const validateMessage = () => {
    if (!messageText.trim()) {
      setMessageError('Please enter a message.');
      return false;
    }

    setMessageError('');
    return true;
  };

  // --------------------------------
  // Generate AI suggestion
  // --------------------------------

  const handleGenerateSuggestion = async () => {
    setError('');
    setSuggestedReply('');
    setGenerationStarted(true);

    const recipientValid = validateRecipient();
    const messageValid = validateMessage();

    if (!recipientValid || !messageValid) {
      setGenerationStarted(false);
      return;
    }

    try {
      setLoading(true);

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Your session has expired. Please log in again.'
        );
      }

      const conversation = await createConversation(
        token,
        `WhatsApp - ${recipient.trim()}`
      );

      if (!conversation || !conversation.id) {
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
            (current) => current + chunk
          );
        }
      );

      generatedReply = generatedReply.trim();

      if (!generatedReply) {
        throw new Error(
          'The AI returned an empty response. Please try again.'
        );
      }

      setSuggestedReply(generatedReply);

      showNotification(
        'AI reply generated successfully.',
        'success'
      );

    } catch (error) {
      setSuggestedReply('');

      const errorMessage =
        error?.message ||
        'Unable to generate an AI reply. Please try again.';

      setError(errorMessage);

      showNotification(errorMessage, 'error');

    } finally {
      setLoading(false);
      setGenerationStarted(false);
    }
  };

  // --------------------------------
  // Use AI suggestion
  // --------------------------------

  const handleUseSuggestion = () => {
    const suggestion = suggestedReply.trim();

    if (!suggestion) {
      return;
    }

    setMessageText(suggestion);
    setMessageError('');
    setError('');
  };

  // --------------------------------
  // Copy AI suggestion
  // --------------------------------

  const handleCopySuggestion = async () => {
    const suggestion = suggestedReply.trim();

    if (!suggestion) {
      return;
    }

    try {
      setCopying(true);

      await Clipboard.setStringAsync(suggestion);

      setError('');

      showNotification(
        'AI suggestion copied successfully.',
        'success'
      );

    } catch (error) {
      setError(
        'Unable to copy the AI suggestion. Please try again.'
      );

    } finally {
      setCopying(false);
    }
  };

  // --------------------------------
  // AI suggestion display
  // --------------------------------

  const renderSuggestionState = () => {
    if (loading && !suggestedReply) {
      return (
        <View style={styles.loadingContainer}>
          <NIRALoader
            message="Generating AI reply..."
            size="small"
          />
        </View>
      );
    }

    if (loading && suggestedReply) {
      return (
        <View>
          <View
            style={styles.suggestionContainer}
            accessible
            accessibilityLabel={
              `AI suggested reply: ${suggestedReply}`
            }
          >
            <Text style={styles.suggestionText}>
              {suggestedReply}
            </Text>
          </View>

          <NIRALoader
            message="Receiving AI response..."
            size="small"
          />
        </View>
      );
    }

    if (suggestedReply) {
      return (
        <View>
          <View
            style={styles.suggestionContainer}
            accessible
          >
            <Text style={styles.suggestionText}>
              {suggestedReply}
            </Text>
          </View>

          <View style={styles.actionRow}>
            <View style={styles.actionButton}>
              <NIRAButton
                title="Use Suggestion"
                variant="secondary"
                onPress={handleUseSuggestion}
                disabled={copying}
              />
            </View>

            <View style={styles.actionButton}>
              <NIRAButton
                title="Copy"
                variant="secondary"
                onPress={handleCopySuggestion}
                disabled={copying}
                loading={copying}
              />
            </View>
          </View>
        </View>
      );
    }

    return (
      <NIRAEmptyState
        title="No AI suggestion yet"
        message="Enter a message and select Generate AI Reply to create a suggested response."
      />
    );
  };

  // --------------------------------
  // Main screen
  // --------------------------------

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={
        Platform.OS === 'ios' ? 'padding' : 'height'
      }
      keyboardVerticalOffset={
        Platform.OS === 'ios' ? 8 : 0
      }
    >
      <NotificationBanner
        visible={notification.visible}
        type={notification.type}
        message={notification.message}
        onDismiss={dismissNotification}
      />

      {/* Header */}

      <View style={styles.header}>
        <Pressable
          style={styles.backButton}
          onPress={onBack}
          disabled={loading}
          accessibilityRole="button"
          accessibilityLabel="Go back"
          accessibilityHint="Return to the home screen"
          accessibilityState={{
            disabled: loading,
          }}
        >
          <Text style={styles.backButtonText}>
            Back
          </Text>
        </Pressable>

        <View style={styles.headerContent}>
          <NIRAHeader
            title="WhatsApp Assistant"
            subtitle="Prepare WhatsApp messages with AI"
          />
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingHorizontal: horizontalPadding,
          },
          contentMaxWidth
            ? {
                width: '100%',
                maxWidth: contentMaxWidth,
                alignSelf: 'center',
              }
            : null,
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        keyboardDismissMode={
          Platform.OS === 'ios'
            ? 'interactive'
            : 'on-drag'
        }
      >
        {/* Global error */}

        {error ? (
          <View
            style={styles.errorContainer}
            accessible
            accessibilityRole="alert"
            accessibilityLabel={`Error: ${error}`}
          >
            <Text style={styles.errorText}>
              {error}
            </Text>
          </View>
        ) : null}

        <View style={styles.content}>

          {/* Recipient */}

          <NIRACard style={styles.card}>
            <Text style={styles.sectionTitle}>
              Recipient
            </Text>

            <Text style={styles.label}>
              Phone number
            </Text>

            <TextInput
              style={[
                styles.input,
                recipientError && styles.inputError,
              ]}
              value={recipient}
              onChangeText={handleRecipientChange}
              placeholder="+91 9876543210"
              placeholderTextColor={COLORS.textSecondary}
              keyboardType="phone-pad"
              editable={!loading}
              autoCapitalize="none"
              accessibilityLabel="WhatsApp recipient phone number"
              accessibilityHint="Enter a phone number including the country code"
              accessibilityState={{
                disabled: loading,
              }}
            />

            {recipientError ? (
              <Text
                style={styles.fieldErrorText}
                accessibilityRole="alert"
              >
                {recipientError}
              </Text>
            ) : null}

            <Text style={styles.helperText}>
              Enter the WhatsApp recipient's phone number,
              including the country code.
            </Text>
          </NIRACard>

          {/* Message */}

          <NIRACard style={styles.card}>
            <View style={styles.messageHeader}>
              <Text style={styles.sectionTitle}>
                Message
              </Text>

              <Text style={styles.characterCounter}>
                {messageText.length}/2000
              </Text>
            </View>

            <TextInput
              style={[
                styles.messageInput,
                messageError && styles.messageInputError,
              ]}
              value={messageText}
              onChangeText={handleMessageChange}
              placeholder="Type your WhatsApp message..."
              placeholderTextColor={COLORS.textSecondary}
              multiline
              maxLength={2000}
              editable={!loading}
              textAlignVertical="top"
              accessibilityLabel="WhatsApp message"
              accessibilityHint="Enter the message you want the AI to use to generate a reply"
              accessibilityState={{
                disabled: loading,
              }}
            />

            {messageError ? (
              <Text
                style={styles.fieldErrorText}
                accessibilityRole="alert"
              >
                {messageError}
              </Text>
            ) : (
              <Text style={styles.helperText}>
                Write the message you want to send or use
                as context for an AI-generated reply.
              </Text>
            )}
          </NIRACard>

          {/* Reply language */}

          <NIRACard style={styles.card}>
            <Text style={styles.sectionTitle}>
              Reply Language
            </Text>

            <View style={styles.languageContainer}>
              <Text style={styles.languageLabel}>
                AI response language
              </Text>

              <NIRABadge
                label={activeLanguage.toUpperCase()}
                color={COLORS.primary}
              />
            </View>

            <Text style={styles.languageDescription}>
              AI-generated replies will use your selected
              communication language. Change your preferred
              language from your profile settings.
            </Text>
          </NIRACard>

          {/* AI suggestion */}

          <NIRACard style={styles.card}>
            <View style={styles.messageHeader}>
              <Text style={styles.sectionTitle}>
                AI Suggested Reply
              </Text>

              <NIRABadge
                label={activeLanguage.toUpperCase()}
                color={COLORS.accent}
              />
            </View>

            {renderSuggestionState()}

            <Text style={styles.languageHint}>
              Generated in {activeLanguage}
            </Text>
          </NIRACard>

          {/* Generate button */}

          <NIRAButton
            title="Generate AI Reply"
            onPress={handleGenerateSuggestion}
            disabled={loading}
            loading={loading}
            style={styles.generateButton}
            accessibilityHint="Generates an AI suggested response using your message"
            accessibilityState={{
              disabled: loading,
              busy: loading,
            }}
          />

          <Text style={styles.disclaimerText}>
            This step generates an AI suggestion.
            WhatsApp sending is not connected yet.
          </Text>

        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// --------------------------------
// Styles
// --------------------------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },

  backButton: {
    minWidth: 48,
    minHeight: 48,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.sm,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },

  backButtonText: {
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.primary,
  },

  headerContent: {
    flex: 1,
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    paddingBottom: SPACING.xxxl,
  },

  content: {
    padding: SPACING.lg,
  },

  card: {
    marginBottom: SPACING.md,
  },

  sectionTitle: {
    fontSize: TYPOGRAPHY.subtitle,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },

  label: {
    fontSize: TYPOGRAPHY.small,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },

  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.md,
    fontSize: TYPOGRAPHY.body,
    backgroundColor: COLORS.surface,
    color: COLORS.text,
  },

  inputError: {
    borderColor: COLORS.error,
  },

  fieldErrorText: {
    marginTop: SPACING.sm,
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.error,
  },

  helperText: {
    marginTop: 7,
    fontSize: TYPOGRAPHY.caption,
    lineHeight: 18,
    color: COLORS.textSecondary,
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
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.md,
    paddingBottom: SPACING.md,
    fontSize: TYPOGRAPHY.body,
    lineHeight: 22,
    backgroundColor: COLORS.surface,
    color: COLORS.text,
  },

  messageInputError: {
    borderColor: COLORS.error,
  },

  characterCounter: {
    marginBottom: 14,
    fontSize: 12,
    color: COLORS.textSecondary,
  },

  languageContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.background,
    padding: SPACING.md,
  },

  languageLabel: {
    fontSize: TYPOGRAPHY.small,
    color: COLORS.text,
    fontWeight: '600',
  },

  languageDescription: {
    marginTop: 9,
    fontSize: TYPOGRAPHY.caption,
    lineHeight: 18,
    color: COLORS.textSecondary,
  },

  loadingContainer: {
    minHeight: 90,
    justifyContent: 'center',
  },

  suggestionContainer: {
    minHeight: 90,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    backgroundColor: COLORS.background,
  },

  suggestionText: {
    fontSize: TYPOGRAPHY.body,
    lineHeight: 23,
    color: COLORS.text,
  },

  actionRow: {
    flexDirection: 'row',
    marginTop: SPACING.md,
    gap: SPACING.sm,
  },

  actionButton: {
    flex: 1,
  },

  languageHint: {
    marginTop: SPACING.md,
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
  },

  generateButton: {
    marginTop: SPACING.sm,
  },

  errorContainer: {
    padding: SPACING.md,
    backgroundColor: '#FDECEC',
    borderBottomWidth: 1,
    borderBottomColor: '#F5C6C6',
  },

  errorText: {
    color: COLORS.error,
    fontSize: TYPOGRAPHY.small,
  },

  disclaimerText: {
    marginTop: 10,
    marginBottom: 8,
    textAlign: 'center',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.textSecondary,
  },
});