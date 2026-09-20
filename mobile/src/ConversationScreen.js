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
  createMessage,
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


export default function ConversationScreen({
  conversation,
  preferredLanguage,
  onBack,
}) {
  const audioRecorder = useAudioRecorder(
    RecordingPresets.HIGH_QUALITY
  );

  const ttsPlayer = useAudioPlayer(null);
  const ttsPlayerStatus = useAudioPlayerStatus(ttsPlayer);
  
  const recorderState = useAudioRecorderState(
    audioRecorder
  );

  console.log(
    'CONVERSATION SCREEN PROP:',
    conversation
  );

  console.log(
    'PREFERRED LANGUAGE PROP:',
    preferredLanguage
  );

  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [playingMessageId, setPlayingMessageId] = useState(null);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

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

  const handleVoicePress = async () => {
    console.log('VOICE BUTTON PRESSED');

    if (requestingMicrophonePermission) {
      return;
    }

    // Stop recording and send the audio to STT.
    if (recorderState.isRecording) {
      try {
        console.log(
          'VOICE RECORDING STOPPING'
        );

        await audioRecorder.stop();

        setRecording(false);

        const recordedUri =
          audioRecorder.uri;

        console.log(
          'VOICE RECORDING STOPPED:',
          recordedUri
        );

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

        console.log(
          'SENDING AUDIO TO STT:',
          language
        );

        const transcription =
          await transcribeAudio(
            token,
            recordedUri,
            language
          );

        console.log(
          'STT TRANSCRIPTION:',
          transcription
        );

        // Put transcription into the input box.
        // Do NOT send automatically.
        setMessageText(transcription);
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

    // Start recording.
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

      console.log(
        'VOICE RECORDING STARTED'
      );
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

  const flatListRef = useRef(null);

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


  const scrollToBottom = () => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({
        animated: true,
      });
    }, 100);
  };


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

        await streamAIMessage(
          token,
          conversation.id,
          content,
          preferredLanguage,
          (chunk) => {
            setMessages(
              (currentMessages) =>
                currentMessages.map(
                  (message) =>
                    message.id ===
                    temporaryAssistantId
                      ? {
                          ...message,
                          content:
                            message.content +
                            chunk,
                        }
                      : message
                )
            );
          }
        );

        /*
         * Streaming is complete.
         * Fetch the authoritative message history
         * from the backend and completely replace
         * the temporary local messages.
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
                  playingMessageId !== item.id ? (
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
          flatListRef.current?.scrollToEnd(
            {
              animated: true,
            }
          );
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
                with the AI assistant.
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
          styles={styles.voiceErrorText}
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
            placeholder="Type a message..."
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
              color="#ffffff"
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
                color="#ffffff"
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
              color="#ffffff"
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
    backgroundColor: '#f5f5f5',
  },

  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },

  statusText: {
    marginTop: 10,
    color: '#666666',
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
  },

  headerContent: {
    flex: 1,
  },

  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
  },

  errorContainer: {
    padding: 12,
    backgroundColor: '#ffecec',
    borderBottomWidth: 1,
    borderBottomColor: '#ffcccc',
  },

  errorText: {
    color: '#b00020',
    marginBottom: 8,
  },

  retryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#b00020',
  },

  retryButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },

  messageList: {
    padding: 12,
    paddingBottom: 20,
  },

  emptyMessageList: {
    flexGrow: 1,
  },

  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 30,
  },

  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },

  emptySubtitle: {
    textAlign: 'center',
    color: '#666666',
    fontSize: 15,
  },

  messageRow: {
    width: '100%',
    marginBottom: 10,
  },

  userMessageRow: {
    alignItems: 'flex-end',
  },

  assistantMessageRow: {
    alignItems: 'flex-start',
  },

  messageBubble: {
    maxWidth: '82%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },

  userBubble: {
    backgroundColor: '#dbeafe',
    borderBottomRightRadius: 4,
  },

  assistantBubble: {
    backgroundColor: '#ffffff',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e2e2e2',
  },

  senderLabel: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },

  userSenderLabel: {
    color: '#2563eb',
  },

  assistantSenderLabel: {
    color: '#555555',
  },

  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },

  userMessageText: {
    color: '#111827',
  },

  assistantMessageText: {
    color: '#222222',
  },

  ttsButton: {
    marginTop: 8,
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },

  ttsButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },

  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },

  timestamp: {
    fontSize: 11,
  },

  userTimestamp: {
    color: '#64748b',
  },

  assistantTimestamp: {
    color: '#888888',
  },

  temporaryLoader: {
    marginLeft: 6,
  },

  editContainer: {
    width: '100%',
  },

  editInput: {
    minHeight: 80,
    maxHeight: 180,
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 10,
    backgroundColor: '#ffffff',
    padding: 10,
    fontSize: 15,
    textAlignVertical: 'top',
  },

  editActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },

  editActionButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },

  cancelEditButton: {
    backgroundColor: '#eeeeee',
  },

  saveEditButton: {
    backgroundColor: '#2563eb',
    minWidth: 60,
    alignItems: 'center',
  },

  cancelEditText: {
    color: '#333333',
    fontWeight: '600',
  },

  saveEditText: {
    color: '#ffffff',
    fontWeight: '600',
  },

  composerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 10,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#dddddd',
  },

  inputWrapper: {
    flex: 1,
    position: 'relative',
    marginRight: 8,
  },

  voiceButton: {
    minWidth: 70,
    height: 48,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },

  voiceButtonDisabled: {
    opacity: 0.5,
  },

  voiceButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },

  voiceErrorText: {
    marginBottom: 8,
    fontSize: 13,
    fontWeight: '500',
  },

  voiceButtonRecording: {
    backgroundColor: '#dc2626',
  },

  messageInput: {
    minHeight: 48,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 14,
    backgroundColor: '#ffffff',
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 24,
    fontSize: 16,
  },

  characterCounter: {
    position: 'absolute',
    right: 10,
    bottom: 6,
    fontSize: 11,
    color: '#888888',
  },

  sendButton: {
    minWidth: 70,
    height: 48,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
  },

  sendButtonDisabled: {
    opacity: 0.5,
  },

  sendButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
