import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  TextInput,
  View,
} from 'react-native';

import { getCurrentUser, logout } from './auth';
import { getProfile, updateProfile } from './profile';
import { getLanguages } from './languages';
import {
  archiveConversation,
  createConversation,
  deleteConversation,
  getConversations,
  getTrashConversations,
  restoreConversation,
  unarchiveConversation,
} from './conversations';

import ConversationScreen from './ConversationScreen';
import WhatsAppScreen from './WhatsAppScreen';
import PhoneCallScreen from './PhoneCallScreen';

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from './storage';

export default function HomeScreen({ onLogout }) {
  const [user, setUser] = useState(null);

  const [isEditingProfile, setIsEditingProfile] =
    useState(false);
  const [languages, setLanguages] =
    useState([]);
  const [showVoiceLanguagePicker, setShowVoiceLanguagePicker] =
    useState(false);

  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    preferred_language: '',
    voice_language: '',
    timezone: '',
  });

  const [userPreferences, setUserPreferences] = useState({
    preferred_language: '',
    voice_language: '',
    timezone: '',
  });

  const [isSavingProfile, setIsSavingProfile] =
    useState(false);

  const [showPreferredLanguagePicker, setShowPreferredLanguagePicker] =
    useState(false);

  const [conversations, setConversations] =
    useState([]);

  const [archivedConversations, setArchivedConversations] =
    useState([]);

  const [trashConversations, setTrashConversations] =
    useState([]);

  const [conversationTitle, setConversationTitle] =
    useState('');

  const [searchText, setSearchText] =
    useState('');

  const [activeView, setActiveView] =
    useState('active');

  const [selectedConversation, setSelectedConversation] =
    useState(null);

  const [showWhatsApp, setShowWhatsApp] =
    useState(false);
  
  const [showPhoneCall, setShowPhoneCall] = useState(false);  

  const [creatingConversation, setCreatingConversation] =
    useState(false);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [loadingConversations, setLoadingConversations] =
    useState(false);

  const [error, setError] =
    useState('');

  const [conversationActionId, setConversationActionId] =
    useState(null);
   
  /*
   * Normalize conversation objects coming from the API.
   */
  const normalizeConversation = (
    conversation
  ) => {
    if (!conversation) {
      return null;
    }

    const conversationId =
      conversation.id ??
      conversation.pk ??
      conversation.conversation_id;

    return {
      ...conversation,
      id: conversationId,
    };
  };

  const getConversationId = (
    conversation
  ) => {
    return (
      conversation?.id ??
      conversation?.pk ??
      conversation?.conversation_id ??
      null
    );
  };

  const getConversationList = (
    conversationData
  ) => {
    const list =
      conversationData?.results ||
      conversationData ||
      [];

    if (!Array.isArray(list)) {
      return [];
    }

    return list
      .map(normalizeConversation)
      .filter(Boolean);
  };

  const loadAllConversations = async (
    token,
    search = searchText
  ) => {
    const [
      activeData,
      archivedData,
      trashData,
    ] = await Promise.all([
      getConversations(token, {
        archived: false,
        search,
      }),

      getConversations(token, {
        archived: true,
        search,
      }),

      getTrashConversations(
        token,
        search
      ),
    ]);

    setConversations(
      getConversationList(activeData)
    );

    setArchivedConversations(
      getConversationList(archivedData)
    );

    setTrashConversations(
      getConversationList(trashData)
    );
  };

  /*
   * Load authenticated user and profile details.
   */
  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const token = await getAccessToken();

        if (!token) {
          throw new Error(
            'Authentication token not found.'
          );
        }

        const data = await getCurrentUser(
          token
        );

        setUser(data);

        try {
          const languageData =
            await getLanguages();

          setLanguages(
            Array.isArray(languageData)
              ? languageData
              : []
          );
        } catch (languageError) {
          console.warn(
            'Unable to load languages:',
            languageError.message
          );
        }

        try {
          const profile = await getProfile(
            token
          );

          console.log(
            'User profile preferences:',
            profile
          );

          setProfileForm({
            first_name:
              profile.first_name || '',
            last_name:
              profile.last_name || '',
            preferred_language:
              profile.preferred_language || '',
            voice_language:
              profile.voice_language || '',
            timezone:
              profile.timezone || '',
          });

          setUserPreferences({
            preferred_language:
              profile.preferred_language || '',
            voice_language:
              profile.voice_language || '',
            timezone:
              profile.timezone || '',
          });
        } catch (profileError) {
          console.warn(
            'Unable to load profile details:',
            profileError.message
          );
        }

        await loadAllConversations(token);
      } catch (err) {
        setError(
          err.message ||
          'Unable to load your profile.'
        );
      } finally {
        setLoading(false);
      }
    };

    loadCurrentUser();
  }, []);

  /*
   * Update a single profile field.
   */
  const handleProfileFieldChange = (
    field,
    value
  ) => {
    setProfileForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }));
  };

  const getLanguageLabel = (languageCode) => {
    const language = languages.find(
      (item) => item.code == languageCode
    );

    if (!language) {
      return languageCode || 'Not set';
    }

    if (
      language.native_name &&
      language.native_name !== language.name
    ) {
      return `${language.name} (${language.native_name})`;
    }

    return language.name;
  };

  /*
   * Cancel profile editing.
   */
  const handleCancelProfileEdit = () => {
    setIsEditingProfile(false);
  };

  /*
   * Save profile changes.
   */
  const handleSaveProfile = async () => {
    try {
      setIsSavingProfile(true);
      setError('');

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const updates = {
        first_name:
          profileForm.first_name.trim(),

        last_name:
          profileForm.last_name.trim(),

        preferred_language:
          profileForm.preferred_language
            .trim()
            .toLowerCase(),

        voice_language:
          profileForm.voice_language
            .trim()
            .toLowerCase(),

        timezone:
          profileForm.timezone.trim(),
      };

      const updatedProfile =
        await updateProfile(
          token,
          updates
        );

      setUserPreferences({
        preferred_language:
          updatedProfile.preferred_language || '',
        voice_language:
          updatedProfile.voice_language || '',
        timezone:
          updatedProfile.timezone || '',
      });

      setProfileForm({
        first_name:
          updatedProfile.first_name || '',

        last_name:
          updatedProfile.last_name || '',

        preferred_language:
          updatedProfile.preferred_language || '',

        voice_language:
          updatedProfile.voice_language || '',

        timezone:
          updatedProfile.timezone || '',
      });

      setUser((currentUser) => ({
        ...currentUser,
        ...updatedProfile,
      }));

      setIsEditingProfile(false);

      Alert.alert(
        'Profile updated',
        'Your profile has been updated successfully.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to update profile',
        err.message ||
        'Your profile could not be updated.'
      );
    } finally {
      setIsSavingProfile(false);
    }
  };

  const refreshConversations = async () => {
    try {
      setRefreshing(true);
      setError('');

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await loadAllConversations(
        token,
        searchText
      );
    } catch (err) {
      setError(
        err.message ||
        'Unable to refresh conversations.'
      );
    } finally {
      setRefreshing(false);
    }
  };

  const handleSearch = async (
    value
  ) => {
    setSearchText(value);

    try {
      setLoadingConversations(true);
      setError('');

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await loadAllConversations(
        token,
        value
      );
    } catch (err) {
      setError(
        err.message ||
        'Unable to search conversations.'
      );
    } finally {
      setLoadingConversations(false);
    }
  };

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

      await loadAllConversations(
        token,
        searchText
      );

      Alert.alert(
        'Conversation created',
        'Your new conversation has been created.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to create conversation',
        err.message ||
        'The conversation could not be created.'
      );
    } finally {
      setCreatingConversation(false);
    }
  };

  const handleArchive = async (
    conversation
  ) => {
    const conversationId =
      getConversationId(conversation);

    if (!conversationId) {
      Alert.alert(
        'Unable to archive',
        'Conversation ID is missing.'
      );
      return;
    }

    try {
      setConversationActionId(
        conversationId
      );

      const token =
        await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await archiveConversation(
        token,
        conversationId
      );

      await loadAllConversations(
        token,
        searchText
      );

      Alert.alert(
        'Conversation archived',
        'The conversation was moved to Archived.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to archive conversation',
        err.message
      );
    } finally {
      setConversationActionId(null);
    }
  };

  const handleUnarchive = async (
    conversation
  ) => {
    const conversationId =
      getConversationId(conversation);

    if (!conversationId) {
      Alert.alert(
        'Unable to restore',
        'Conversation ID is missing.'
      );
      return;
    }

    try {
      setConversationActionId(
        conversationId
      );

      const token =
        await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      await unarchiveConversation(
        token,
        conversationId
      );

      await loadAllConversations(
        token,
        searchText
      );

      Alert.alert(
        'Conversation restored',
        'The conversation was moved back to Active.'
      );
    } catch (err) {
      Alert.alert(
        'Unable to restore conversation',
        err.message
      );
    } finally {
      setConversationActionId(null);
    }
  };

  const handleDelete = (
    conversation
  ) => {
    const conversationId =
      getConversationId(conversation);

    if (!conversationId) {
      Alert.alert(
        'Unable to delete',
        'Conversation ID is missing.'
      );
      return;
    }

    Alert.alert(
      'Move to trash?',
      `Move "${conversation.title}" to trash?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Move to Trash',
          style: 'destructive',
          onPress: async () => {
            try {
              setConversationActionId(
                conversationId
              );

              const token =
                await getAccessToken();

              if (!token) {
                throw new Error(
                  'Authentication token not found.'
                );
              }

              await deleteConversation(
                token,
                conversationId
              );

              if (
                getConversationId(
                  selectedConversation
                ) === conversationId
              ) {
                setSelectedConversation(null);
              }

              await loadAllConversations(
                token,
                searchText
              );

              Alert.alert(
                'Moved to trash',
                'The conversation is now in Trash.'
              );
            } catch (err) {
              Alert.alert(
                'Unable to delete conversation',
                err.message
              );
            } finally {
              setConversationActionId(null);
            }
          },
        },
      ]
    );
  };

  const handleRestore = (
    conversation
  ) => {
    const conversationId =
      getConversationId(conversation);

    if (!conversationId) {
      Alert.alert(
        'Unable to restore',
        'Conversation ID is missing.'
      );
      return;
    }

    Alert.alert(
      'Restore conversation?',
      `Restore "${conversation.title}"?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Restore',
          onPress: async () => {
            try {
              setConversationActionId(
                conversationId
              );

              const token =
                await getAccessToken();

              if (!token) {
                throw new Error(
                  'Authentication token not found.'
                );
              }

              await restoreConversation(
                token,
                conversationId
              );

              await loadAllConversations(
                token,
                searchText
              );

              Alert.alert(
                'Conversation restored',
                'The conversation has been restored.'
              );
            } catch (err) {
              Alert.alert(
                'Unable to restore conversation',
                err.message
              );
            } finally {
              setConversationActionId(null);
            }
          },
        },
      ]
    );
  };

  const handleLogout = async () => {
    try {
      const accessToken =
        await getAccessToken();

      const refreshToken =
        await getRefreshToken();

      if (
        accessToken &&
        refreshToken
      ) {
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

  const getCurrentList = () => {
    if (activeView === 'archived') {
      return archivedConversations;
    }

    if (activeView === 'trash') {
      return trashConversations;
    }

    return conversations;
  };

  const currentConversations =
    getCurrentList();

  const getEmptyMessage = () => {
    if (searchText.trim()) {
      return 'No conversations match your search.';
    }

    if (activeView === 'archived') {
      return 'No archived conversations.';
    }

    if (activeView === 'trash') {
      return 'Trash is empty.';
    }

    return 'No conversations yet.';
  };

  const handleConversationPress = (
    conversation
  ) => {
    if (activeView === 'trash') {
      return;
    }

    const normalizedConversation =
      normalizeConversation(
        conversation
      );

    const conversationId =
      getConversationId(
        normalizedConversation
      );

    if (!conversationId) {
      console.log(
        'OPEN CONVERSATION ERROR:',
        normalizedConversation
      );

      Alert.alert(
        'Unable to open conversation',
        'Conversation ID is missing from the API response.'
      );

      return;
    }

    console.log(
      'OPEN CONVERSATION:',
      conversationId
    );

    setSelectedConversation({
      ...normalizedConversation,
      id: conversationId,
    });
  };

  const handleConversationAction = (
    conversation
  ) => {
    if (activeView === 'active') {
      Alert.alert(
        conversation.title,
        'Choose an action',
        [
          {
            text: 'Open',
            onPress: () =>
              handleConversationPress(
                conversation
              ),
          },
          {
            text: 'Archive',
            onPress: () =>
              handleArchive(
                conversation
              ),
          },
          {
            text: 'Move to Trash',
            style: 'destructive',
            onPress: () =>
              handleDelete(
                conversation
              ),
          },
          {
            text: 'Cancel',
            style: 'cancel',
          },
        ]
      );

      return;
    }

    if (activeView === 'archived') {
      Alert.alert(
        conversation.title,
        'Choose an action',
        [
          {
            text: 'Open',
            onPress: () =>
              handleConversationPress(
                conversation
              ),
          },
          {
            text: 'Move to Active',
            onPress: () =>
              handleUnarchive(
                conversation
              ),
          },
          {
            text: 'Move to Trash',
            style: 'destructive',
            onPress: () =>
              handleDelete(
                conversation
              ),
          },
          {
            text: 'Cancel',
            style: 'cancel',
          },
        ]
      );

      return;
    }

    handleRestore(conversation);
  };

  /*
   * Open WhatsApp Assistant.
   */
  const handleOpenWhatsApp = () => {
    setError('');
    setShowWhatsApp(true);
  };

  const handleOpenPhoneCall = () => {
    setError('');
    setShowPhoneCall(true);
  };

  /*
   * Return from WhatsApp Assistant.
   */
  const handleCloseWhatsApp = () => {
    setShowWhatsApp(false);
  };

  const handleClosePhoneCall = () => {
    setShowPhoneCall(false);
  };

  if (selectedConversation) {
    return (
      <ConversationScreen
        conversation={selectedConversation}
        preferredLanguage={
          userPreferences.preferred_language
        }
        onBack={() =>
          setSelectedConversation(null)
        }
      />
    );
  }

  if (showWhatsApp) {
    return (
      <WhatsAppScreen
        preferredLanguage={
          userPreferences.preferred_language
        }
        onBack={handleCloseWhatsApp}
      />
    );
  }

  if (showPhoneCall) {
    return (
      <PhoneCallScreen
        preferredLanguage={
          userPreferences.preferred_language
        }
        onBack={handleClosePhoneCall}
      />  
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator
          size="large"
        />

        <Text style={styles.loadingText}>
          Loading your profile...
        </Text>
      </View>
    );
  }

  if (error && !user) {
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
          <Text
            style={
              styles.logoutButtonText
            }
          >
            Sign Out
          </Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={
        styles.container
      }
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={
            refreshConversations
          }
        />
      }
    >
      <Text style={styles.title}>
        AI Communication Assistant
      </Text>

      <Text style={styles.subtitle}>
        Welcome back!
      </Text>

      {/* PROFILE CARD */}
      <View style={styles.card}>
        <View style={styles.profileHeader}>
          <Text style={styles.cardTitle}>
            Your profile
          </Text>

          {!isEditingProfile ? (
            <Pressable
              style={styles.editProfileButton}
              onPress={() =>
                setIsEditingProfile(true)
              }
            >
              <Text
                style={
                  styles.editProfileButtonText
                }
              >
                Edit
              </Text>
            </Pressable>
          ) : null}
        </View>

        {!isEditingProfile ? (
          <>
            <Text style={styles.cardText}>
              Username:{' '}
              {user?.username || 'N/A'}
            </Text>

            <Text style={styles.cardText}>
              Email:{' '}
              {user?.email || 'N/A'}
            </Text>

            <Text style={styles.cardText}>
              Name:{' '}
              {profileForm.first_name ||
              profileForm.last_name
                ? `${profileForm.first_name} ${profileForm.last_name}`.trim()
                : 'Not set'}
            </Text>

            <Text style={styles.cardText}>
              Preferred language:{' '}
              {profileForm.preferred_language ||
                'Not set'}
            </Text>

            <Text style={styles.cardText}>
              Voice language:{' '}
              {profileForm.voice_language ||
                'Not set'}
            </Text>

            <Text style={styles.cardText}>
              Timezone:{' '}
              {profileForm.timezone ||
                'Not set'}
            </Text>
          </>
        ) : (
          <>
            <Text style={styles.formLabel}>
              First name
            </Text>

            <TextInput
              style={styles.profileInput}
              placeholder="Enter first name"
              value={
                profileForm.first_name
              }
              onChangeText={(value) =>
                handleProfileFieldChange(
                  'first_name',
                  value
                )
              }
              editable={
                !isSavingProfile
              }
            />

            <Text style={styles.formLabel}>
              Last name
            </Text>

            <TextInput
              style={styles.profileInput}
              placeholder="Enter last name"
              value={
                profileForm.last_name
              }
              onChangeText={(value) =>
                handleProfileFieldChange(
                  'last_name',
                  value
                )
              }
              editable={
                !isSavingProfile
              }
            />

            <Text style={styles.formLabel}>
              Preferred language
            </Text>

            <Pressable
              style={styles.languageSelector}
              onPress={() =>
                setShowPreferredLanguagePicker(
                  (current) => !current
                )
              }
              disabled={isSavingProfile}
            >
              <Text
                style={
                  styles.languageSelectorText
                }
              >
                {getLanguageLabel(
                  profileForm.preferred_language
                )}
              </Text>

              <Text
                style={
                  styles.languageSelectorArrow
                }
              >
                {showPreferredLanguagePicker
                  ? '▲'
                  : '▼'}
              </Text>
            </Pressable>

            {showPreferredLanguagePicker ? (
              <View
                style={
                  styles.languageOptions
                }
              >
                {languages.map((language) => (
                  <Pressable
                    key={language.id}
                    style={
                      styles.languageOption
                    }
                    onPress={() => {
                      handleProfileFieldChange(
                        'preferred_language',
                        language.code
                      );

                      setShowPreferredLanguagePicker(
                        false
                      );
                    }}
                  >
                    <Text
                      style={
                        styles.languageOptionName
                      }
                    >
                      {language.name}
                    </Text>

                    <Text
                      style={
                        styles.languageOptionNative
                      }
                    >
                      {language.native_name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}

            <Text style={styles.formLabel}>
              Voice language
            </Text>

            <Pressable
              style={styles.languageSelector}
              onPress={() =>
                setShowVoiceLanguagePicker(
                  (current) => !current
                )
              }
              disabled={isSavingProfile}
            >
              <Text
                style={
                  styles.languageSelectorText
                }
              >
                {getLanguageLabel(
                  profileForm.voice_language
                )}
              </Text>

              <Text
                style={
                  styles.languageSelectorArrow
                }
              >
                {showVoiceLanguagePicker
                  ? '▲'
                  : '▼'}
              </Text>
            </Pressable>

            {showVoiceLanguagePicker ? (
              <View
                style={
                  styles.languageOptions
                }
              >
                {languages.map((language) => (
                  <Pressable
                    key={language.id}
                    style={
                      styles.languageOption
                    }
                    onPress={() => {
                      handleProfileFieldChange(
                        'voice_language',
                        language.code
                      );

                      setShowVoiceLanguagePicker(
                        false
                      );
                    }}
                  >
                    <Text
                      style={
                        styles.languageOptionName
                      }
                    >
                      {language.name}
                    </Text>

                    <Text
                      style={
                        styles.languageOptionNative
                      }
                    >
                      {language.native_name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}

            <Text style={styles.formHint}>
              Use the language code configured by the backend.
            </Text>

            <Text style={styles.formLabel}>
              Timezone
            </Text>

            <TextInput
              style={styles.profileInput}
              placeholder="Example: Asia/Kolkata"
              value={
                profileForm.timezone
              }
              onChangeText={(value) =>
                handleProfileFieldChange(
                  'timezone',
                  value
                )
              }
              autoCapitalize="none"
              autoCorrect={false}
              editable={
                !isSavingProfile
              }
            />

            <View style={styles.profileActions}>
              <Pressable
                style={
                  styles.cancelProfileButton
                }
                onPress={
                  handleCancelProfileEdit
                }
                disabled={
                  isSavingProfile
                }
              >
                <Text
                  style={
                    styles.cancelProfileButtonText
                  }
                >
                  Cancel
                </Text>
              </Pressable>

              <Pressable
                style={[
                  styles.saveProfileButton,
                  isSavingProfile &&
                    styles.buttonDisabled,
                ]}
                onPress={
                  handleSaveProfile
                }
                disabled={
                  isSavingProfile
                }
              >
                {isSavingProfile ? (
                  <ActivityIndicator
                    size="small"
                  />
                ) : (
                  <Text
                    style={
                      styles.saveProfileButtonText
                    }
                  >
                    Save Changes
                  </Text>
                )}
              </Pressable>
            </View>
          </>
        )}
      </View>

      {/* WHATSAPP ASSISTANT */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          WhatsApp Assistant
        </Text>

        <Text style={styles.communicationDescription}>
          Prepare WhatsApp messages with an
          AI-generated reply in your preferred
          language.
        </Text>

        <Pressable
          style={styles.whatsappButton}
          onPress={handleOpenWhatsApp}
        >
          <Text
            style={
              styles.whatsappButtonText
            }
          >
            Open WhatsApp Assistant
          </Text>
        </Pressable>

        <Text style={styles.communicationHint}>
          WhatsApp sending is not connected yet.
        </Text>
      </View>

      <View style={styles.communicationCard}>
        <Text style={styles.communicationTitle}>
          Phone Call Assistant
        </Text>

        <Text style={styles.communicationDescription}>
          Prepare AI-assisted responses for
          phone conversations.
        </Text>

        <TouchableOpacity
          style={styles.phoneCallButton}
          onPress={handleOpenPhoneCall}
        >
          <Text style={styles.phoneCallButtonText}>
            Open Phone Call Assistant
          </Text>
        </TouchableOpacity>

        <Text style={styles.communicationHint}>
          Phone calling is not connected yet.
        </Text>
      </View>

      {/* NEW CONVERSATION */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          New conversation
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Enter conversation title"
          value={conversationTitle}
          onChangeText={
            setConversationTitle
          }
          autoCapitalize="sentences"
          editable={
            !creatingConversation
          }
        />

        <Pressable
          style={[
            styles.createButton,
            creatingConversation &&
              styles.buttonDisabled,
          ]}
          onPress={
            handleCreateConversation
          }
          disabled={
            creatingConversation
          }
        >
          <Text
            style={
              styles.createButtonText
            }
          >
            {creatingConversation
              ? 'Creating...'
              : 'New Conversation'}
          </Text>
        </Pressable>
      </View>

      {/* CONVERSATIONS */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Conversations
        </Text>

        <TextInput
          style={styles.searchInput}
          placeholder="Search conversations..."
          value={searchText}
          onChangeText={handleSearch}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <View style={styles.tabs}>
          <Pressable
            style={[
              styles.tab,
              activeView === 'active' &&
                styles.activeTab,
            ]}
            onPress={() =>
              setActiveView('active')
            }
          >
            <Text
              style={[
                styles.tabText,
                activeView ===
                  'active' &&
                  styles.activeTabText,
              ]}
            >
              Active
            </Text>
          </Pressable>

          <Pressable
            style={[
              styles.tab,
              activeView ===
                'archived' &&
                styles.activeTab,
            ]}
            onPress={() =>
              setActiveView(
                'archived'
              )
            }
          >
            <Text
              style={[
                styles.tabText,
                activeView ===
                  'archived' &&
                  styles.activeTabText,
              ]}
            >
              Archived
            </Text>
          </Pressable>

          <Pressable
            style={[
              styles.tab,
              activeView === 'trash' &&
                styles.activeTab,
            ]}
            onPress={() =>
              setActiveView('trash')
            }
          >
            <Text
              style={[
                styles.tabText,
                activeView ===
                  'trash' &&
                  styles.activeTabText,
              ]}
            >
              Trash
            </Text>
          </Pressable>
        </View>

        {loadingConversations ? (
          <View style={styles.listLoading}>
            <ActivityIndicator />

            <Text
              style={
                styles.listLoadingText
              }
            >
              Searching...
            </Text>
          </View>
        ) : currentConversations.length ===
          0 ? (
          <View style={styles.emptyState}>
            <Text
              style={
                styles.emptyStateTitle
              }
            >
              {getEmptyMessage()}
            </Text>

            <Text
              style={
                styles.emptyStateText
              }
            >
              {activeView ===
                'active' &&
              !searchText.trim()
                ? 'Create a new conversation to get started.'
                : activeView ===
                    'trash'
                  ? 'Deleted conversations will appear here.'
                  : 'Conversations in this section will appear here.'}
            </Text>
          </View>
        ) : (
          currentConversations.map(
            (conversation) => {
              const conversationId =
                getConversationId(
                  conversation
                );

              const actionInProgress =
                conversationActionId ===
                conversationId;

              return (
                <Pressable
                  key={
                    conversationId ??
                    `conversation-${conversation.title}-${conversation.created_at}`
                  }
                  style={[
                    styles.conversationItem,
                    actionInProgress &&
                      styles.itemDisabled,
                  ]}
                  onPress={() =>
                    handleConversationPress(
                      conversation
                    )
                  }
                  onLongPress={() =>
                    handleConversationAction(
                      conversation
                    )
                  }
                  disabled={
                    actionInProgress ||
                    !conversationId
                  }
                >
                  <View
                    style={
                      styles.conversationContent
                    }
                  >
                    <Text
                      style={
                        styles.conversationTitle
                      }
                      numberOfLines={1}
                    >
                      {conversation.title}
                    </Text>

                    <Text
                      style={
                        styles.conversationDate
                      }
                    >
                      {conversation.created_at}
                    </Text>
                  </View>

                  {actionInProgress ? (
                    <ActivityIndicator
                      size="small"
                    />
                  ) : (
                    <Text
                      style={
                        styles.actionHint
                      }
                    >
                      ⋯
                    </Text>
                  )}
                </Pressable>
              );
            }
          )
        )}

        <Text style={styles.actionHelp}>
          Tap to open. Long press for actions.
        </Text>
      </View>

      {error ? (
        <View style={styles.inlineError}>
          <Text
            style={styles.inlineErrorText}
          >
            {error}
          </Text>

          <Pressable
            onPress={
              refreshConversations
            }
          >
            <Text
              style={styles.retryText}
            >
              Retry
            </Text>
          </Pressable>
        </View>
      ) : null}

      <Pressable
        style={styles.logoutButton}
        onPress={handleLogout}
      >
        <Text
          style={
            styles.logoutButtonText
          }
        >
          Sign Out
        </Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
    backgroundColor: '#f5f7fb',
  },

  container: {
    paddingHorizontal: 24,
    paddingTop: 90,
    paddingBottom: 40,
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

  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  editProfileButton: {
    borderWidth: 1,
    borderColor: '#111827',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 16,
  },

  editProfileButtonText: {
    color: '#111827',
    fontSize: 14,
    fontWeight: '600',
  },

  cardText: {
    fontSize: 15,
    color: '#374151',
    marginBottom: 8,
  },

  formLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 7,
  },

  profileInput: {
    height: 50,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 15,
    fontSize: 16,
    backgroundColor: '#ffffff',
    marginBottom: 6,
  },

  formHint: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 14,
  },

  languageSelector: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    marginBottom: 6,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  languageSelectorText: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
  },

  languageSelectorArrow: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 10,
  },

  languageOptions: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    marginBottom: 14,
    overflow: 'hidden',
  },

  languageOption: {
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },

  languageOptionName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },

  languageOptionNative: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 3,
  },

  profileActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },

  cancelProfileButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
  },

  cancelProfileButtonText: {
    color: '#374151',
    fontSize: 15,
    fontWeight: '600',
  },

  saveProfileButton: {
    flex: 1,
    backgroundColor: '#111827',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },

  saveProfileButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
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

  searchInput: {
    height: 50,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    backgroundColor: '#ffffff',
    marginBottom: 16,
  },

  /*
   * WhatsApp Assistant styles.
   */
  communicationDescription: {
    fontSize: 14,
    lineHeight: 20,
    color: '#4b5563',
    marginBottom: 16,
  },

  whatsappButton: {
    backgroundColor: '#2563eb',
    borderRadius: 12,
    paddingVertical: 16,
  },

  whatsappButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    textAlign: 'center',
  },

  phoneCallButton: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
  },

  phoneCallButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },

  communicationHint: {
    marginTop: 9,
    fontSize: 12,
    lineHeight: 18,
    color: '#9ca3af',
    textAlign: 'center',
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

  tabs: {
    flexDirection: 'row',
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    padding: 4,
    marginBottom: 16,
  },

  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 9,
    alignItems: 'center',
  },

  activeTab: {
    backgroundColor: '#111827',
  },

  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },

  activeTabText: {
    color: '#ffffff',
  },

  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingVertical: 14,
  },

  conversationContent: {
    flex: 1,
    paddingRight: 12,
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

  actionHint: {
    fontSize: 24,
    color: '#6b7280',
    paddingHorizontal: 4,
  },

  actionHelp: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 12,
  },

  itemDisabled: {
    opacity: 0.5,
  },

  listLoading: {
    alignItems: 'center',
    paddingVertical: 24,
  },

  listLoadingText: {
    marginTop: 8,
    fontSize: 13,
    color: '#6b7280',
  },

  emptyState: {
    alignItems: 'center',
    paddingVertical: 28,
    paddingHorizontal: 12,
  },

  emptyStateTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
    marginBottom: 8,
  },

  emptyStateText: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    lineHeight: 20,
  },

  inlineError: {
    backgroundColor: '#fee2e2',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },

  inlineErrorText: {
    color: '#b91c1c',
    fontSize: 14,
    marginBottom: 8,
  },

  retryText: {
    color: '#991b1b',
    fontSize: 14,
    fontWeight: '700',
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
    marginBottom: 20,
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
