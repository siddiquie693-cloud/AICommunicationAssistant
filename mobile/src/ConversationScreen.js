import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import * as Clipboard from 'expo-clipboard';

import { formatMessageTime } from './formatters';
import {
  deleteMessage,
  getMessages,
  streamAIMessage,
  updateMessage,
} from './messages';
import { getAccessToken } from './storage';

export default function ConversationScreen({
  conversation,
  onBack,
}) {
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editingText, setEditingText] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const [deletingMessageId, setDeletingMessageId] =
    useState(null);

  const flatListRef = useRef(null);

  const loadMessages = async (showLoader = true) => {
    try {
      if (showLoader) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError('');

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const data = await getMessages(
        token,
        conversation.id
      );

      setMessages(data?.results || data || []);
    } catch (err) {
      setError(
        err.message ||
        'Unable to load messages.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [conversation.id]);

  const handleRefreshMessages = async () => {
    await loadMessages(false);
  };

  const handleCopyMessage = async (content) => {
    try {
      await Clipboard.setStringAsync(content);

      Alert.alert(
        'Copied',
        'Message copied to clipboard.'
      );
    } catch (error) {
      Alert.alert(
        'Unable to copy',
        'The message could not be copied.'
      );
    }
  };

  const startEditingMessage = (message) => {
    setEditingMessageId(message.id);
    setEditingText(message.content);
  };

  const cancelEditing = () => {
    setEditingMessageId(null);
    setEditingText('');
    setSavingEdit(false);
  };

  const handleSaveEdit = async () => {
    const content = editingText.trim();

    if (!content) {
      Alert.alert(
        'Invalid message',
        'Message cannot be empty.'
      );
      return;
    }

    if (content.length > 2000) {
      Alert.alert(
        'Message too long',
        'Message cannot exceed 2000 characters.'
      );
      return;
    }

    if (savingEdit) {
      return;
    }

    try {
      setSavingEdit(true);

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const updatedMessage =
        await updateMessage(
          token,
          conversation.id,
          editingMessageId,
          content
        );

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === editingMessageId
            ? {
                ...message,
                ...(updatedMessage || {}),
                content,
              }
            : message
        )
      );

      cancelEditing();

      Alert.alert(
        'Message updated',
        'Your message was updated successfully.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to update message',
        err.message ||
          'The message could not be updated.'
      );
      setSavingEdit(false);
    }
  };

  const confirmDeleteMessage = (message) => {
    Alert.alert(
      'Delete message',
      'Are you sure you want to delete this message?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () =>
            handleDeleteMessage(message.id),
        },
      ]
    );
  };

  const handleDeleteMessage = async (messageId) => {
    if (deletingMessageId) {
      return;
    }

    try {
      setDeletingMessageId(messageId);

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await deleteMessage(
        token,
        conversation.id,
        messageId
      );

      setMessages((currentMessages) =>
        currentMessages.filter(
          (message) =>
            message.id !== messageId
        )
      );

      if (editingMessageId === messageId) {
        cancelEditing();
      }
    } catch (err) {
      Alert.alert(
        'Unable to delete message',
        err.message ||
          'The message could not be deleted.'
      );
    } finally {
      setDeletingMessageId(null);
    }
  };

  const handleMessageLongPress = (message) => {
    const actions = [
      {
        text: 'Copy',
        onPress: () =>
          handleCopyMessage(message.content),
      },
    ];

    if (message.sender_type === 'user') {
      actions.push({
        text: 'Edit',
        onPress: () =>
          startEditingMessage(message),
      });
    }

    actions.push({
      text: 'Delete',
      style: 'destructive',
      onPress: () =>
        confirmDeleteMessage(message),
    });

    actions.push({
      text: 'Cancel',
      style: 'cancel',
    });

    Alert.alert(
      'Message actions',
      'Choose an action',
      actions
    );
  };

  const handleSendMessage = async () => {
    const content = messageText.trim();

    if (!content || sending) {
      return;
    }

    if (content.length > 2000) {
      Alert.alert(
        'Message too long',
        'Message cannot exceed 2000 characters.'
      );
      return;
    }

    try {
      setSending(true);
      setError('');
      setMessageText('');

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const temporaryUserMessage = {
        id: `temporary-user-${Date.now()}`,
        sender_type: 'user',
        content,
        created_at: new Date().toISOString(),
        isTemporary: true,
      };

      const temporaryAssistantId =
        `temporary-assistant-${Date.now()}`;

      const temporaryAssistantMessage = {
        id: temporaryAssistantId,
        sender_type: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        isTemporary: true,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        temporaryUserMessage,
        temporaryAssistantMessage,
      ]);

      await streamAIMessage(
        token,
        conversation.id,
        content,
        (chunk) => {
          setMessages((currentMessages) =>
            currentMessages.map((message) =>
              message.id === temporaryAssistantId
                ? {
                    ...message,
                    content:
                      message.content + chunk,
                  }
                : message
            )
          );
        }
      );

      await loadMessages(false);
    } catch (err) {
      setMessageText(content);

      setMessages((currentMessages) =>
        currentMessages.filter(
          (message) =>
            !message.isTemporary
        )
      );

      Alert.alert(
        'Unable to send message',
        err.message ||
          'The message could not be sent.'
      );
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      flatListRef.current?.scrollToEnd({
        animated: true,
      });
    });
  };

  const renderMessage = ({ item }) => {
    const isUser =
      item.sender_type === 'user';

    const isEditing =
      editingMessageId === item.id;

    const isDeleting =
      deletingMessageId === item.id;

    if (isEditing) {
      return (
        <View style={styles.editContainer}>
          <Text style={styles.editLabel}>
            Edit message
          </Text>

          <TextInput
            value={editingText}
            onChangeText={setEditingText}
            multiline
            maxLength={2000}
            autoFocus
            editable={!savingEdit}
            style={styles.editInput}
            textAlignVertical="top"
          />

          <View style={styles.editFooter}>
            <Text style={styles.characterCounter}>
              {editingText.length}/2000
            </Text>

            <View style={styles.editActions}>
              <Pressable
                style={styles.cancelButton}
                onPress={cancelEditing}
                disabled={savingEdit}
              >
                <Text style={styles.cancelButtonText}>
                  Cancel
                </Text>
              </Pressable>

              <Pressable
                style={styles.saveButton}
                onPress={handleSaveEdit}
                disabled={
                  savingEdit ||
                  !editingText.trim()
                }
              >
                {savingEdit ? (
                  <ActivityIndicator
                    size="small"
                    color="#ffffff"
                  />
                ) : (
                  <Text style={styles.saveButtonText}>
                    Save
                  </Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      );
    }

    return (
      <View
        style={[
          styles.messageRow,
          isUser
            ? styles.userRow
            : styles.assistantRow,
        ]}
      >
        <Pressable
          onLongPress={() =>
            handleMessageLongPress(item)
          }
          delayLongPress={400}
          disabled={isDeleting}
          style={[
            styles.messageBubble,
            isUser
              ? styles.userBubble
              : styles.assistantBubble,
          ]}
        >
          <Text
            style={[
              styles.senderLabel,
              isUser
                ? styles.userSenderLabel
                : styles.assistantSenderLabel,
            ]}
          >
            {isUser ? 'You' : 'AI Assistant'}
          </Text>

          <Text
            style={[
              styles.messageText,
              isUser
                ? styles.userMessageText
                : styles.assistantMessageText,
            ]}
          >
            {item.content}
          </Text>

          <Text
            style={[
              styles.timestamp,
              isUser
                ? styles.userTimestamp
                : styles.assistantTimestamp,
            ]}
          >
            {formatMessageTime(
              item.created_at
            )}
          </Text>

          {isDeleting && (
            <View style={styles.deleteOverlay}>
              <ActivityIndicator
                size="small"
                color="#ffffff"
              />
            </View>
          )}
        </Pressable>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator
          size="large"
          color="#2563eb"
        />

        <Text style={styles.loadingText}>
          Loading messages...
        </Text>
      </View>
    );
  }

  if (error && messages.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorTitle}>
          Unable to load conversation
        </Text>

        <Text style={styles.errorText}>
          {error}
        </Text>

        <Pressable
          style={styles.retryButton}
          onPress={() => loadMessages()}
        >
          <Text style={styles.retryButtonText}>
            Retry
          </Text>
        </Pressable>

        <Pressable
          style={styles.backButton}
          onPress={onBack}
        >
          <Text style={styles.backButtonText}>
            Back
          </Text>
        </Pressable>
      </View>
    );
  }

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
        <Pressable
          onPress={onBack}
          style={styles.headerBackButton}
        >
          <Text style={styles.headerBackText}>
            ‹
          </Text>
        </Pressable>

        <View style={styles.headerTitleContainer}>
          <Text
            style={styles.headerTitle}
            numberOfLines={1}
          >
            {conversation.title}
          </Text>

          <Text style={styles.headerSubtitle}>
            AI Communication Assistant
          </Text>
        </View>

        <Pressable
          onPress={handleRefreshMessages}
          disabled={refreshing}
          style={styles.refreshButton}
        >
          {refreshing ? (
            <ActivityIndicator
              size="small"
              color="#2563eb"
            />
          ) : (
            <Text style={styles.refreshText}>
              ↻
            </Text>
          )}
        </Pressable>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) =>
          String(item.id)
        }
        renderItem={renderMessage}
        contentContainerStyle={[
          styles.messagesContainer,
          messages.length === 0 &&
            styles.emptyMessagesContainer,
        ]}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={scrollToBottom}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>
              💬
            </Text>

            <Text style={styles.emptyTitle}>
              No messages yet
            </Text>

            <Text style={styles.emptyText}>
              Start the conversation by
              sending a message below.
            </Text>
          </View>
        }
      />

      <View style={styles.composerContainer}>
        <View style={styles.inputWrapper}>
          <TextInput
            value={messageText}
            onChangeText={setMessageText}
            placeholder="Type a message..."
            placeholderTextColor="#9ca3af"
            multiline
            maxLength={2000}
            editable={!sending}
            style={styles.input}
            textAlignVertical="top"
          />

          <Text style={styles.characterCounter}>
            {messageText.length}/2000
          </Text>
        </View>

        <Pressable
          onPress={handleSendMessage}
          disabled={
            sending ||
            !messageText.trim()
          }
          style={[
            styles.sendButton,
            (sending ||
              !messageText.trim()) &&
              styles.sendButtonDisabled,
          ]}
        >
          {sending ? (
            <ActivityIndicator
              size="small"
              color="#ffffff"
            />
          ) : (
            <Text style={styles.sendButtonText}>
              Send
            </Text>
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },

  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },

  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#64748b',
  },

  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#f8fafc',
  },

  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 8,
    textAlign: 'center',
  },

  errorText: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 20,
  },

  retryButton: {
    minWidth: 120,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    marginBottom: 10,
  },

  retryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },

  backButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
  },

  backButtonText: {
    color: '#2563eb',
    fontSize: 15,
    fontWeight: '600',
  },

  header: {
    minHeight: 68,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    flexDirection: 'row',
    alignItems: 'center',
  },

  headerBackButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },

  headerBackText: {
    fontSize: 34,
    color: '#2563eb',
    lineHeight: 38,
  },

  headerTitleContainer: {
    flex: 1,
    marginHorizontal: 8,
  },

  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0f172a',
  },

  headerSubtitle: {
    marginTop: 2,
    fontSize: 11,
    color: '#64748b',
  },

  refreshButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },

  refreshText: {
    fontSize: 25,
    color: '#2563eb',
  },

  messagesContainer: {
    paddingHorizontal: 12,
    paddingVertical: 16,
  },

  emptyMessagesContainer: {
    flexGrow: 1,
    justifyContent: 'center',
  },

  emptyContainer: {
    alignItems: 'center',
    paddingHorizontal: 30,
  },

  emptyIcon: {
    fontSize: 42,
    marginBottom: 12,
  },

  emptyTitle: {
    fontSize: 19,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 6,
  },

  emptyText: {
    fontSize: 14,
    lineHeight: 21,
    color: '#64748b',
    textAlign: 'center',
  },

  messageRow: {
    width: '100%',
    marginBottom: 10,
    flexDirection: 'row',
  },

  userRow: {
    justifyContent: 'flex-end',
  },

  assistantRow: {
    justifyContent: 'flex-start',
  },

  messageBubble: {
    maxWidth: '82%',
    minWidth: 80,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 16,
    overflow: 'hidden',
  },

  userBubble: {
    backgroundColor: '#2563eb',
    borderBottomRightRadius: 4,
  },

  assistantBubble: {
    backgroundColor: '#ffffff',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },

  senderLabel: {
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 4,
  },

  userSenderLabel: {
    color: '#dbeafe',
  },

  assistantSenderLabel: {
    color: '#64748b',
  },

  messageText: {
    fontSize: 15,
    lineHeight: 21,
  },

  userMessageText: {
    color: '#ffffff',
  },

  assistantMessageText: {
    color: '#0f172a',
  },

  timestamp: {
    fontSize: 10,
    marginTop: 5,
  },

  userTimestamp: {
    color: '#bfdbfe',
    textAlign: 'right',
  },

  assistantTimestamp: {
    color: '#94a3b8',
    textAlign: 'right',
  },

  deleteOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
  },

  editContainer: {
    width: '100%',
    marginBottom: 12,
    padding: 12,
    backgroundColor: '#ffffff',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#93c5fd',
  },

  editLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#2563eb',
    marginBottom: 8,
  },

  editInput: {
    minHeight: 80,
    maxHeight: 180,
    padding: 10,
    borderRadius: 10,
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    color: '#0f172a',
    fontSize: 15,
  },

  editFooter: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  editActions: {
    flexDirection: 'row',
    gap: 8,
  },

  cancelButton: {
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: 9,
    backgroundColor: '#e2e8f0',
  },

  cancelButtonText: {
    color: '#334155',
    fontWeight: '600',
  },

  saveButton: {
    minWidth: 70,
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: 9,
    backgroundColor: '#2563eb',
    alignItems: 'center',
  },

  saveButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },

  composerContainer: {
    padding: 10,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },

  inputWrapper: {
    flex: 1,
    position: 'relative',
  },

  input: {
    minHeight: 48,
    maxHeight: 120,
    paddingTop: 12,
    paddingBottom: 25,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    color: '#0f172a',
    fontSize: 15,
  },

  characterCounter: {
    fontSize: 10,
    color: '#94a3b8',
  },

  inputWrapper: {
    flex: 1,
    position: 'relative',
  },

  sendButton: {
    minWidth: 72,
    height: 48,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
  },

  sendButtonDisabled: {
    backgroundColor: '#94a3b8',
  },

  sendButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});