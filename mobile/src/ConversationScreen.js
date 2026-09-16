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

import { formatMessageTime } from './formatters';
import { getMessages, streamAIMessage } from './messages';
import { getAccessToken } from './storage';

export default function ConversationScreen({
  conversation,
  onBack,
}) {
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const flatListRef = useRef(null);

  const loadMessages = async (token) => {
    const messageData = await getMessages(
      token,
      conversation.id
    );

    setMessages(
      messageData.results ||
      messageData
    );
  };

  useEffect(() => {
    const loadConversationMessages = async () => {
      try {
        const token = await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        await loadMessages(token);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadConversationMessages();
  }, [conversation.id]);

  const handleSendMessage = async () => {
    const content = messageText.trim();

    if (!content || sending) {
      return;
    }

    try {
      setSending(true);

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      setMessageText('');

      const temporaryUserMessage = {
        id: `user-${Date.now()}`,
        sender_type: 'user',
        content,
        created_at: new Date().toISOString(),
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        temporaryUserMessage,
      ]);

      const temporaryAssistantId =
        `assistant-${Date.now()}`;

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: temporaryAssistantId,
          sender_type: 'assistant',
          content: '',
          created_at: new Date().toISOString(),
        },
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
    } catch (err) {
      Alert.alert(
        'Unable to send message',
        err.message
      );
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />

        <Text style={styles.loadingText}>
          Loading messages...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Pressable
            style={styles.backButton}
            onPress={onBack}
          >
            <Text style={styles.backButtonText}>
              ← Back
            </Text>
          </Pressable>

          <Text
            style={styles.title}
            numberOfLines={1}
          >
            {conversation.title}
          </Text>
        </View>

        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            Unable to load messages
          </Text>

          <Text style={styles.errorText}>
            {error}
          </Text>
        </View>
      </View>
    );
  }

  const sendDisabled =
    !messageText.trim() || sending;

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
          style={styles.backButton}
          onPress={onBack}
        >
          <Text style={styles.backButtonText}>
            ← Back
          </Text>
        </Pressable>

        <Text
          style={styles.title}
          numberOfLines={1}
        >
          {conversation.title}
        </Text>
      </View>

      <FlatList
        ref={flatListRef}
        style={styles.messagesContainer}
        contentContainerStyle={
          messages.length === 0
            ? styles.emptyList
            : styles.messageList
        }
        data={messages}
        keyExtractor={(item) =>
          String(item.id)
        }
        onContentSizeChange={() => {
          flatListRef.current?.scrollToEnd({
            animated: true,
          });
        }}
        renderItem={({ item }) => {
          const isUser =
            item.sender_type === 'user';

          return (
            <View
              style={[
                styles.messageRow,
                isUser
                  ? styles.userRow
                  : styles.assistantRow,
              ]}
            >
              <View
                style={[
                  styles.messageBubble,
                  isUser
                    ? styles.userBubble
                    : styles.assistantBubble,
                ]}
              >
                <Text
                  style={[
                    styles.senderType,
                    isUser
                      ? styles.userSenderType
                      : styles.assistantSenderType,
                  ]}
                >
                  {isUser
                    ? 'You'
                    : 'Assistant'}
                </Text>

                <Text
                  style={[
                    styles.messageContent,
                    isUser
                      ? styles.userMessageContent
                      : styles.assistantMessageContent,
                  ]}
                >
                  {item.content}
                </Text>

                <Text
                  style={[
                    styles.messageDate,
                    isUser
                      ? styles.userMessageDate
                      : styles.assistantMessageDate,
                  ]}
                >
                  {formatMessageTime(
                    item.created_at
                  )}
                </Text>
              </View>
            </View>
          );
        }}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle}>
              No messages yet
            </Text>

            <Text style={styles.emptyText}>
              Send a message to start the conversation.
            </Text>
          </View>
        }
      />

      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <TextInput
            style={styles.messageInput}
            placeholder="Type a message..."
            placeholderTextColor="#9ca3af"
            value={messageText}
            onChangeText={setMessageText}
            multiline
            maxLength={2000}
            editable={!sending}
            textAlignVertical="top"
          />

          <Text style={styles.characterCount}>
            {messageText.length}/2000
          </Text>
        </View>

        <Pressable
          style={[
            styles.sendButton,
            sendDisabled &&
              styles.buttonDisabled,
          ]}
          onPress={handleSendMessage}
          disabled={sendDisabled}
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
    backgroundColor: '#f5f7fb',
  },

  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
    backgroundColor: '#f5f7fb',
  },

  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },

  backButton: {
    alignSelf: 'flex-start',
    marginBottom: 14,
  },

  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },

  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
  },

  messagesContainer: {
    flex: 1,
    paddingHorizontal: 14,
  },

  messageList: {
    paddingVertical: 20,
  },

  emptyList: {
    flexGrow: 1,
    paddingHorizontal: 10,
  },

  messageRow: {
    width: '100%',
    marginBottom: 12,
  },

  userRow: {
    alignItems: 'flex-end',
  },

  assistantRow: {
    alignItems: 'flex-start',
  },

  messageBubble: {
    maxWidth: '82%',
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },

  userBubble: {
    backgroundColor: '#111827',
    borderBottomRightRadius: 4,
  },

  assistantBubble: {
    backgroundColor: '#ffffff',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },

  senderType: {
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 5,
    textTransform: 'uppercase',
  },

  userSenderType: {
    color: '#d1d5db',
  },

  assistantSenderType: {
    color: '#6b7280',
  },

  messageContent: {
    fontSize: 16,
    lineHeight: 23,
    marginBottom: 7,
  },

  userMessageContent: {
    color: '#ffffff',
  },

  assistantMessageContent: {
    color: '#111827',
  },

  messageDate: {
    fontSize: 10,
  },

  userMessageDate: {
    color: '#9ca3af',
  },

  assistantMessageDate: {
    color: '#9ca3af',
  },

  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },

  emptyText: {
    fontSize: 15,
    color: '#6b7280',
    textAlign: 'center',
  },

  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },

  inputWrapper: {
    flex: 1,
    marginRight: 10,
  },

  messageInput: {
    minHeight: 48,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#ffffff',
  },

  characterCount: {
    alignSelf: 'flex-end',
    marginTop: 4,
    marginRight: 4,
    fontSize: 11,
    color: '#9ca3af',
  },

  sendButton: {
    minWidth: 72,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111827',
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 15,
  },

  sendButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },

  buttonDisabled: {
    opacity: 0.45,
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
});