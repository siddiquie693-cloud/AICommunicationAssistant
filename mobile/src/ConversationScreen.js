import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

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
  TouchableOpacity,
  View,
} from 'react-native';

import * as Clipboard from 'expo-clipboard';

import {
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
  useAudioPlayer,
  useAudioPlayerStatus,
  RecordingPresets,
} from 'expo-audio';

import {
  deleteMessage,
  getMessages,
  streamAIMessage,
  updateMessage,
} from './messages';

import {
  transcribeAudio,
  synthesizeSpeech,
} from './speech';

import {
  formatMessageTime,
} from './formatters';

import {
  getAccessToken,
} from './storage';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from './theme';

export default function ConversationScreen({
  conversation,
  preferredLanguage,
  onBack,
}) {
  const audioRecorder = useAudioRecorder(
    RecordingPresets.HIGH_QUALITY
  );

  const ttsPlayer = useAudioPlayer(null);
  const ttsPlayerStatus =
    useAudioPlayerStatus(ttsPlayer);

  const recorderState =
    useAudioRecorderState(
      audioRecorder
    );

  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] =
    useState('');
  const [loading, setLoading] =
    useState(true);
  const [refreshing, setRefreshing] =
    useState(false);
  const [sending, setSending] =
    useState(false);
  const [error, setError] =
    useState('');
  const [playingMessageId, setPlayingMessageId] =
    useState(null);
  const [voiceLoading, setVoiceLoading] =
    useState(false);
  const [voiceError, setVoiceError] =
    useState('');
  const [recording, setRecording] =
    useState(false);
  const [transcribing, setTranscribing] =
    useState(false);

  const [
    requestingMicrophonePermission,
    setRequestingMicrophonePermission,
  ] = useState(false);

  const [editingMessageId, setEditingMessageId] =
    useState(null);

  const [editingText, setEditingText] =
    useState('');

  const [savingMessageId, setSavingMessageId] =
    useState(null);

  const [deletingMessageId, setDeletingMessageId] =
    useState(null);

  const flatListRef = useRef(null);

  /*
   * Streaming performance:
   *
   * AI providers can return many small chunks.
   * Updating React state for every chunk causes
   * unnecessary FlatList renders.
   *
   * These refs accumulate chunks and flush them
   * to React at a controlled interval.
   */
  const streamingBufferRef = useRef('');
  const streamingFlushTimerRef = useRef(null);
  const streamingAssistantIdRef = useRef(null);

  /*
   * Scroll performance:
   *
   * The message list can change many times while
   * an AI response streams. Throttle automatic
   * scrolling so it does not execute for every
   * rendered chunk.
   */
  const scrollTimerRef = useRef(null);

  const clearStreamingFlushTimer =
    useCallback(() => {
      if (
        streamingFlushTimerRef.current !== null
      ) {
        clearTimeout(
          streamingFlushTimerRef.current
        );

        streamingFlushTimerRef.current =
          null;
      }
    }, []);

  const flushStreamingBuffer =
    useCallback(() => {
      const bufferedText =
        streamingBufferRef.current;

      const assistantId =
        streamingAssistantIdRef.current;

      if (
        !bufferedText ||
        !assistantId
      ) {
        return;
      }

      streamingBufferRef.current = '';

      setMessages(
        (currentMessages) =>
          currentMessages.map(
            (message) =>
              message.id === assistantId
                ? {
                    ...message,
                    content:
                      message.content +
                      bufferedText,
                  }
                : message
          )
      );
    }, []);

  const scheduleStreamingFlush =
    useCallback(() => {
      if (
        streamingFlushTimerRef.current !==
        null
      ) {
        return;
      }

      streamingFlushTimerRef.current =
        setTimeout(() => {
          streamingFlushTimerRef.current =
            null;

          flushStreamingBuffer();
        }, 50);
    }, [flushStreamingBuffer]);

  const appendStreamingChunk =
    useCallback(
      (chunk) => {
        if (!chunk) {
          return;
        }

        streamingBufferRef.current += chunk;

        scheduleStreamingFlush();
      },
      [scheduleStreamingFlush]
    );

  const clearStreamingState =
    useCallback(() => {
      clearStreamingFlushTimer();

      streamingBufferRef.current = '';
      streamingAssistantIdRef.current =
        null;
    }, [clearStreamingFlushTimer]);

  const scrollToBottom = useCallback(
    (animated = true) => {
      if (
        scrollTimerRef.current !== null
      ) {
        return;
      }

      scrollTimerRef.current =
        setTimeout(() => {
          scrollTimerRef.current = null;

          flatListRef.current?.scrollToEnd({
            animated,
          });
        }, 80);
    },
    []
  );

  const handleVoicePress = async () => {
    if (requestingMicrophonePermission) {
      return;
    }

    if (recorderState.isRecording) {
      try {
        await audioRecorder.stop();

        setRecording(false);

        const recordedUri =
          audioRecorder.uri;

        if (!recordedUri) {
          throw new Error(
            'Recorded audio file was not created.'
          );
        }

        const token =
          await getAccessToken();

        if (!token) {
          throw new Error(
            'Your session has expired. Please log in again.'
          );
        }

        setTranscribing(true);
        setVoiceError('');

        const language =
          preferredLanguage || 'en';

        const transcription =
          await transcribeAudio(
            token,
            recordedUri,
            language
          );

        setMessageText(
          transcription
        );
      } catch (err) {
        console.error(
          'VOICE / STT ERROR:',
          err
        );

        setVoiceError(
          err?.message ||
          'Unable to transcribe the recording.'
        );

        Alert.alert(
          'Voice transcription error',
          err?.message ||
            'Unable to transcribe the recording.'
        );
      } finally {
        setTranscribing(false);
        setSending(false);
      }

      return;
    }

    try {
      setRequestingMicrophonePermission(
        true
      );

      setVoiceError('');

      const permission =
        await requestRecordingPermissionsAsync();

      if (!permission.granted) {
        throw new Error(
          'Please allow microphone access to use voice communication.'
        );
      }

      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      await audioRecorder.prepareToRecordAsync();

      audioRecorder.record();

      setRecording(true);
    } catch (err) {
      console.error(
        'VOICE RECORDING ERROR:',
        err
      );

      setRecording(false);

      setVoiceError(
        err?.message ||
        'Unable to start voice recording.'
      );

      Alert.alert(
        'Voice recording error',
        err?.message ||
          'Unable to start voice recording.'
      );
    } finally {
      setRequestingMicrophonePermission(
        false
      );
    }
  };

  const handleTextToSpeech = async (
    messageId,
    text
  ) => {
    try {
      if (
        playingMessageId === messageId &&
        ttsPlayerStatus.playing
      ) {
        ttsPlayer.pause();
        return;
      }

      if (
        playingMessageId === messageId &&
        !ttsPlayerStatus.playing &&
        !ttsPlayerStatus.didJustFinish
      ) {
        ttsPlayer.play();
        return;
      }

      if (
        playingMessageId === messageId &&
        ttsPlayerStatus.didJustFinish
      ) {
        ttsPlayer.play();
        return;
      }

      setVoiceError('');
      setVoiceLoading(true);

      const token =
        await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const audioUri =
        await synthesizeSpeech(
          token,
          text,
          preferredLanguage
        );

      ttsPlayer.replace(audioUri);

      setPlayingMessageId(messageId);

      ttsPlayer.play();
    } catch (err) {
      console.error(
        'TEXT TO SPEECH ERROR:',
        err
      );

      setPlayingMessageId(null);

      setVoiceError(
        err?.message ||
        'Unable to generate speech.'
      );
    } finally {
      setVoiceLoading(false);
    }
  };

  const loadMessages = useCallback(
    async (showLoading = true) => {
      try {
        if (showLoading) {
          setLoading(true);
        } else {
          setRefreshing(true);
        }

        setError('');

        const token =
          await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        const data =
          await getMessages(
            token,
            conversation.id
          );

        const messageList =
          data?.results ||
          data ||
          [];

        const orderedMessages =
          Array.isArray(messageList)
            ? [...messageList].reverse()
            : [];

        setMessages(
          orderedMessages
        );
      } catch (err) {
        setError(
          err?.message ||
          'Failed to load messages.'
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [conversation.id]
  );

  useEffect(() => {
    loadMessages(true);
  }, [loadMessages]);

  useEffect(() => {
    if (
      ttsPlayerStatus.didJustFinish &&
      playingMessageId !== null
    ) {
      setPlayingMessageId(null);
    }
  }, [
    ttsPlayerStatus.didJustFinish,
    playingMessageId,
  ]);

  useEffect(() => {
    return () => {
      clearStreamingState();

      if (
        scrollTimerRef.current !== null
      ) {
        clearTimeout(
          scrollTimerRef.current
        );

        scrollTimerRef.current = null;
      }
    };
  }, [clearStreamingState]);

  const handleRefresh = () => {
    loadMessages(false);
  };

  const handleCopyMessage =
    async (message) => {
      try {
        await Clipboard.setStringAsync(
          message.content || ''
        );

        Alert.alert(
          'Copied',
          'Message copied to clipboard.'
        );
      } catch (err) {
        Alert.alert(
          'Copy failed',
          'Unable to copy this message.'
        );
      }
    };

  const handleEditMessage =
    (message) => {
      setEditingMessageId(
        message.id
      );

      setEditingText(
        message.content || ''
      );
    };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditingText('');
  };

  const handleSaveEdit =
    async (message) => {
      const content =
        editingText.trim();

      if (!content) {
        Alert.alert(
          'Invalid message',
          'Message content cannot be empty.'
        );

        return;
      }

      if (savingMessageId) {
        return;
      }

      try {
        setSavingMessageId(
          message.id
        );

        const token =
          await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        const updatedMessage =
          await updateMessage(
            token,
            conversation.id,
            message.id,
            content
          );

        setMessages(
          (currentMessages) =>
            currentMessages.map(
              (currentMessage) =>
                currentMessage.id ===
                message.id
                  ? {
                      ...currentMessage,
                      ...(updatedMessage ||
                        {}),
                      content,
                    }
                  : currentMessage
            )
        );

        setEditingMessageId(null);
        setEditingText('');
      } catch (err) {
        Alert.alert(
          'Update failed',
          err?.message ||
            'Unable to update message.'
        );
      } finally {
        setSavingMessageId(null);
      }
    };

  const handleDeleteMessage =
    (message) => {
      if (deletingMessageId) {
        return;
      }

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
            onPress: async () => {
              try {
                setDeletingMessageId(
                  message.id
                );

                const token =
                  await getAccessToken();

                if (!token) {
                  throw new Error(
                    'Authentication token not found.'
                  );
                }

                await deleteMessage(
                  token,
                  conversation.id,
                  message.id
                );

                setMessages(
                  (currentMessages) =>
                    currentMessages.filter(
                      (currentMessage) =>
                        currentMessage.id !==
                        message.id
                    )
                );
              } catch (err) {
                Alert.alert(
                  'Delete failed',
                  err?.message ||
                    'Unable to delete message.'
                );
              } finally {
                setDeletingMessageId(
                  null
                );
              }
            },
          },
        ]
      );
    };

  const handleMessageActions =
    (message) => {
      if (message.isTemporary) {
        return;
      }

      const actions = [
        {
          text: 'Copy',
          onPress: () =>
            handleCopyMessage(
              message
            ),
        },
      ];

      if (
        message.sender_type ===
        'user'
      ) {
        actions.push({
          text: 'Edit',
          onPress: () =>
            handleEditMessage(
              message
            ),
        });
      }

      actions.push({
        text: 'Delete',
        style: 'destructive',
        onPress: () =>
          handleDeleteMessage(
            message
          ),
      });

      actions.push({
        text: 'Cancel',
        style: 'cancel',
      });

      Alert.alert(
        'Message actions',
        null,
        actions
      );
    };

  const handleSendMessage =
    async () => {
      const content =
        messageText.trim();

      if (!content || sending) {
        return;
      }

      if (!conversation?.id) {
        Alert.alert(
          'Unable to send',
          'Conversation ID is missing.'
        );

        return;
      }

      setSending(true);
      setError('');
      setMessageText('');

      clearStreamingState();

      try {
        const token =
          await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        const temporaryUserId =
          `temporary-user-${Date.now()}`;

        const temporaryAssistantId =
          `temporary-assistant-${Date.now()}`;

        streamingAssistantIdRef.current =
          temporaryAssistantId;

        const temporaryUserMessage = {
          id: temporaryUserId,
          sender_type: 'user',
          content,
          created_at:
            new Date().toISOString(),
          isTemporary: true,
        };

        const temporaryAssistantMessage = {
          id: temporaryAssistantId,
          sender_type: 'assistant',
          content: '',
          created_at:
            new Date().toISOString(),
          isTemporary: true,
        };

        setMessages(
          (currentMessages) => [
            ...currentMessages,
            temporaryUserMessage,
            temporaryAssistantMessage,
          ]
        );

        scrollToBottom();

        await streamAIMessage(
          token,
          conversation.id,
          content,
          preferredLanguage,
          appendStreamingChunk
        );

        /*
         * Make sure the final buffered
         * streaming content is rendered
         * before replacing it with the
         * authoritative server response.
         */
        clearStreamingFlushTimer();

        flushStreamingBuffer();

        /*
         * Streaming is complete.
         * Fetch the authoritative message
         * history from the backend and
         * completely replace the temporary
         * local messages.
         */
        const latestMessages =
          await getMessages(
            token,
            conversation.id
          );

        const serverMessages =
          latestMessages?.results ||
          latestMessages ||
          [];

        const orderedMessages =
          Array.isArray(
            serverMessages
          )
            ? [...serverMessages].reverse()
            : [];

        setMessages(
          orderedMessages
        );

        scrollToBottom();
      } catch (err) {
        clearStreamingState();

        setMessageText(content);

        setMessages(
          (currentMessages) =>
            currentMessages.filter(
              (message) =>
                !message.isTemporary
            )
        );

        Alert.alert(
          'Message failed',
          err?.message ||
            'Unable to send message.'
        );
      } finally {
        clearStreamingState();
        setSending(false);
      }
    };

  const renderMessage = ({
    item,
  }) => {
    const isUser =
      item.sender_type === 'user';

    const isEditing =
      editingMessageId === item.id;

    const isDeleting =
      deletingMessageId === item.id;

    return (
      <View
        style={[
          styles.messageRow,
          isUser
            ? styles.userMessageRow
            : styles.assistantMessageRow,
        ]}
      >
        <Pressable
          style={[
            styles.messageBubble,
            isUser
              ? styles.userBubble
              : styles.assistantBubble,
          ]}
          onLongPress={() =>
            handleMessageActions(
              item
            )
          }
          delayLongPress={400}
        >
          <Text
            style={[
              styles.senderLabel,
              isUser
                ? styles.userSenderLabel
                : styles.assistantSenderLabel,
            ]}
          >
            {isUser
              ? 'You'
              : 'AI Assistant'}
          </Text>

          {isEditing ? (
            <View
              style={
                styles.editContainer
              }
            >
              <TextInput
                style={
                  styles.editInput
                }
                value={editingText}
                onChangeText={
                  setEditingText
                }
                multiline
                maxLength={2000}
                autoFocus
              />

              <View
                style={
                  styles.editActions
                }
              >
                <Pressable
                  style={[
                    styles.editActionButton,
                    styles.cancelEditButton,
                  ]}
                  onPress={
                    handleCancelEdit
                  }
                  disabled={
                    savingMessageId ===
                    item.id
                  }
                >
                  <Text
                    style={
                      styles.cancelEditText
                    }
                  >
                    Cancel
                  </Text>
                </Pressable>

                <Pressable
                  style={[
                    styles.editActionButton,
                    styles.saveEditButton,
                  ]}
                  onPress={() =>
                    handleSaveEdit(
                      item
                    )
                  }
                  disabled={
                    savingMessageId ===
                    item.id
                  }
                >
                  {savingMessageId ===
                  item.id ? (
                    <ActivityIndicator
                      size="small"
                      color="#ffffff"
                    />
                  ) : (
                    <Text
                      style={
                        styles.saveEditText
                      }
                    >
                      Save
                    </Text>
                  )}
                </Pressable>
              </View>
            </View>
          ) : (
            <View>
              <Text
                style={[
                  styles.messageText,
                  isUser
                    ? styles.userMessageText
                    : styles.assistantMessageText,
                ]}
              >
                {item.content || ''}
              </Text>

              {!isUser && !isEditing && (
                <TouchableOpacity
                  onPress={() =>
                    handleTextToSpeech(
                      item.id,
                      item.content || ''
                    )
                  }
                  style={styles.ttsButton}
                  disabled={voiceLoading}
                >
                  {voiceLoading &&
                  playingMessageId !==
                    item.id ? (
                    <View
                      style={{
                        flexDirection: 'row',
                        alignItems: 'center',
                      }}
                    >
                      <ActivityIndicator
                        size="small"
                      />

                      <Text
                        style={[
                          styles.ttsButtonText,
                          { marginLeft: 6 },
                        ]}
                      >
                        Generating...
                      </Text>
                    </View>
                  ) : (
                    <Text
                      style={
                        styles.ttsButtonText
                      }
                    >
                      {playingMessageId ===
                        item.id &&
                      ttsPlayerStatus.playing
                        ? '⏸ Pause'
                        : playingMessageId ===
                            item.id &&
                          !ttsPlayerStatus.didJustFinish
                        ? '▶️ Resume'
                        : '🔊 Play'}
                    </Text>
                  )}
                </TouchableOpacity>
              )}

              <View
                style={
                  styles.messageFooter
                }
              >
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

                {item.isTemporary && (
                  <ActivityIndicator
                    size="small"
                    style={
                      styles.temporaryLoader
                    }
                  />
                )}

                {isDeleting && (
                  <ActivityIndicator
                    size="small"
                    style={
                      styles.temporaryLoader
                    }
                  />
                )}
              </View>
            </View>
          )}
        </Pressable>
      </View>
    );
  };

  if (loading) {
    return (
      <View
        style={
          styles.centerContainer
        }
      >
        <ActivityIndicator
          size="large"
        />

        <Text
          style={styles.statusText}
        >
          Loading messages...
        </Text>
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
          style={styles.backButton}
          onPress={onBack}
        >
          <Text
            style={
              styles.backButtonText
            }
          >
            Back
          </Text>
        </Pressable>

        <View
          style={
            styles.headerContent
          }
        >
          <Text
            style={styles.headerTitle}
            numberOfLines={1}
          >
            {conversation?.title ||
              'Conversation'}
          </Text>
        </View>
      </View>

      {error && (
        <View
          style={
            styles.errorContainer
          }
        >
          <Text
            style={styles.errorText}
          >
            {error}
          </Text>

          <Pressable
            style={
              styles.retryButton
            }
            onPress={() =>
              loadMessages(true)
            }
          >
            <Text
              style={
                styles.retryButtonText
              }
            >
              Retry
            </Text>
          </Pressable>
        </View>
      )}

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(
          item,
          index
        ) =>
          String(
            item.id ??
            `message-${index}`
          )
        }
        renderItem={
          renderMessage
        }
        contentContainerStyle={[
          styles.messageList,
          messages.length === 0 &&
            styles.emptyMessageList,
        ]}
        refreshing={refreshing}
        onRefresh={handleRefresh}
        onContentSizeChange={() => {
          scrollToBottom();
        }}
        ListEmptyComponent={
          !error ? (
            <View
              style={
                styles.emptyContainer
              }
            >
              <Text
                style={
                  styles.emptyTitle
                }
              >
                No messages yet
              </Text>

              <Text
                style={
                  styles.emptySubtitle
                }
              >
                Start a conversation
                with NIRA AI.
              </Text>
            </View>
          ) : null
        }
      />

      <View
        style={
          styles.composerContainer
        }
      >
        {voiceError ? (
          <Text
            style={styles.voiceErrorText}
          >
            {voiceError}
          </Text>
        ) : null}

        <View
          style={
            styles.inputWrapper
          }
        >
          <TextInput
            style={
              styles.messageInput
            }
            value={messageText}
            onChangeText={
              setMessageText
            }
            placeholder="Message NIRA AI..."
            placeholderTextColor={COLORS.textSecondary}
            multiline
            maxLength={2000}
            editable={!sending}
            textAlignVertical="top"
          />

          <Text
            style={
              styles.characterCounter
            }
          >
            {messageText.length}/2000
          </Text>
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel={recording ? 'Stop voice recording' : 'Start voice recording'}
          style={[
            styles.voiceButton,
            recording &&
              styles.voiceButtonRecording,
            (requestingMicrophonePermission ||
              transcribing) &&
              styles.voiceButtonDisabled,
          ]}
          onPress={handleVoicePress}
          disabled={
            requestingMicrophonePermission ||
            transcribing
          }
        >
          {requestingMicrophonePermission ? (
            <ActivityIndicator
              size="small"
              color={COLORS.white}
            />
          ) : transcribing ? (
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              <ActivityIndicator
                size="small"
                color={COLORS.white}
              />

              <Text
                style={[
                  styles.voiceButtonText,
                  { marginLeft: 6 },
                ]}
              >
                Transcribing...
              </Text>
            </View>
          ) : (
            <Text
              style={styles.voiceButtonText}
            >
              {recording
                ? '🔴 Stop'
                : '🎙️ Voice'}
            </Text>
          )}
        </Pressable>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Send message"
          style={[
            styles.sendButton,
            (
              !messageText.trim() ||
              sending
            ) &&
              styles.sendButtonDisabled,
          ]}
          onPress={
            handleSendMessage
          }
          disabled={
            !messageText.trim() ||
            sending
          }
        >
          {sending ? (
            <ActivityIndicator
              size="small"
              color={COLORS.white}
            />
          ) : (
            <Text
              style={
                styles.sendButtonText
              }
            >
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
    backgroundColor: COLORS.background,
  },

  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },

  statusText: {
    marginTop: SPACING.sm,
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.small,
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
    paddingVertical: SPACING.sm,
    paddingRight: SPACING.md,
  },

  backButtonText: {
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.primary,
  },

  headerContent: {
    flex: 1,
  },

  headerTitle: {
    fontSize: TYPOGRAPHY.subtitle,
    fontWeight: '700',
    color: COLORS.text,
  },

  errorContainer: {
    padding: SPACING.md,
    backgroundColor: '#FFF1F1',
    borderBottomWidth: 1,
    borderBottomColor: '#F5C6C6',
  },

  errorText: {
    color: COLORS.error,
    marginBottom: SPACING.sm,
    fontSize: TYPOGRAPHY.small,
  },

  retryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.error,
  },

  retryButtonText: {
    color: COLORS.white,
    fontWeight: '600',
  },

  messageList: {
    padding: SPACING.md,
    paddingBottom: SPACING.xl,
  },

  emptyMessageList: {
    flexGrow: 1,
  },

  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xxxl,
  },

  emptyTitle: {
    fontSize: TYPOGRAPHY.title,
    fontWeight: '700',
    marginBottom: SPACING.sm,
    color: COLORS.text,
  },

  emptySubtitle: {
    textAlign: 'center',
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.small,
  },

  messageRow: {
    width: '100%',
    marginBottom: SPACING.sm,
  },

  userMessageRow: {
    alignItems: 'flex-end',
  },

  assistantMessageRow: {
    alignItems: 'flex-start',
  },

  messageBubble: {
    maxWidth: '82%',
    borderRadius: RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },

  userBubble: {
    backgroundColor: '#E5F0FF',
    borderBottomRightRadius: RADIUS.sm,
  },

  assistantBubble: {
    backgroundColor: COLORS.surface,
    borderBottomLeftRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  senderLabel: {
    fontSize: TYPOGRAPHY.caption,
    fontWeight: '700',
    marginBottom: SPACING.xs,
  },

  userSenderLabel: {
    color: COLORS.primary,
  },

  assistantSenderLabel: {
    color: COLORS.textSecondary,
  },

  messageText: {
    fontSize: TYPOGRAPHY.body,
    lineHeight: 22,
  },

  userMessageText: {
    color: COLORS.text,
  },

  assistantMessageText: {
    color: COLORS.text,
  },

  ttsButton: {
    marginTop: SPACING.sm,
    alignSelf: 'flex-start',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: RADIUS.md,
    backgroundColor: '#EAF2FC',
  },

  ttsButtonText: {
    fontSize: TYPOGRAPHY.small,
    fontWeight: '600',
    color: COLORS.primary,
  },

  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.sm,
  },

  timestamp: {
    fontSize: TYPOGRAPHY.caption,
  },

  userTimestamp: {
    color: COLORS.textSecondary,
  },

  assistantTimestamp: {
    color: COLORS.textSecondary,
  },

  temporaryLoader: {
    marginLeft: SPACING.sm,
  },

  editContainer: {
    width: '100%',
  },

  editInput: {
    minHeight: 80,
    maxHeight: 180,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    fontSize: TYPOGRAPHY.small,
    color: COLORS.text,
    textAlignVertical: 'top',
  },

  editActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: SPACING.sm,
    gap: SPACING.sm,
  },

  editActionButton: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: RADIUS.md,
  },

  cancelEditButton: {
    backgroundColor: '#EEF1F5',
  },

  saveEditButton: {
    backgroundColor: COLORS.primary,
    minWidth: 60,
    alignItems: 'center',
  },

  cancelEditText: {
    color: COLORS.text,
    fontWeight: '600',
  },

  saveEditText: {
    color: COLORS.white,
    fontWeight: '600',
  },

  composerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },

  inputWrapper: {
    flex: 1,
    position: 'relative',
    marginRight: SPACING.sm,
  },

  voiceButton: {
    minWidth: 70,
    height: 48,
    paddingHorizontal: SPACING.md,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.sm,
  },

  voiceButtonDisabled: {
    opacity: 0.5,
  },

  voiceButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
  },

  voiceErrorText: {
    marginBottom: SPACING.sm,
    fontSize: TYPOGRAPHY.caption,
    fontWeight: '500',
    color: COLORS.error,
  },

  voiceButtonRecording: {
    backgroundColor: COLORS.error,
  },

  messageInput: {
    minHeight: 48,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surface,
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.md,
    paddingBottom: 24,
    fontSize: TYPOGRAPHY.body,
    color: COLORS.text,
  },

  characterCounter: {
    position: 'absolute',
    right: SPACING.md,
    bottom: SPACING.sm,
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
  },

  sendButton: {
    minWidth: 70,
    height: 48,
    paddingHorizontal: SPACING.md,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  sendButtonDisabled: {
    opacity: 0.5,
  },

  sendButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
  },
});
