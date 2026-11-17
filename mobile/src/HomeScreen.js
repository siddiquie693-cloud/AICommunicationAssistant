import { 
  useEffect, 
  useState, 
} from 'react';

import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  TextInput,
  View,
  useWindowDimensions,
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
import NIRAHeader from './components/NIRAHeader';
import NIRACard from './components/NIRACard';
import NIRAButton from './components/NIRAButton';
import NIRAScreen from './NIRAScreen';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from './theme';

export default function HomeScreen({ 
  onLogout,
  onOpenNIRAPersonalProfile,

 }) {
  const {width} = useWindowDimensions();

  const horizontalPadding = width < 360 ? 16 : width < 600 ? 20 : 24;

  const contentMaxWidth = width >= 900 ? 760 : undefined;

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
    <NIRAScreen
      scrollable
      style={[
        styles.scrollView,
        { backgroundColor: COLORS.background },
      ]}
      contentContainerStyle={[
        styles.container,
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
      keyboardDismissMode={
        Platform.OS === 'ios'
          ? 'interactive'
          : "on-drag"
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
      <NIRAHeader
        title="NIRA AI"
        subtitle="Your personal AI assistant"
        onBack={undefined}
      />

      {/* PROFILE CARD */}
      <NIRACard style={styles.card}>
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
              accessibilityRole='button'
              accessibilityLabel='Edit profile'
              accessibilityHint='Opens the profile editor'
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
              accessibilityLabel="First name"
              accessibilityHint="Enter your first name"
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
              accessibilityLabel="Last name"
              accessibilityHint="Enter your last name"
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
              accessibilityRole="button"
              accessibilityLabel={`Preferred language: ${getLanguageLabel(
                profileForm.preferred_language
              )}`}
              accessibilityHint="Opens the preferred language selector"
              accessibilityState={{
                disabled: isSavingProfile,
                expanded: showPreferredLanguagePicker,
              }}
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
                    accessibilityRole="button"
                    accessibilityLabel={`Select ${language.name}${
                      language.native_name
                        ? `, ${language.native_name}`
                        : ''
                    }`}
                    accessibilityState={{
                      selected:
                        profileForm.preferred_language ===
                        language.code,
                    }}
                  
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
              accessibilityLabel={`Voice language: ${getLanguageLabel(
                profileForm.voice_language
              )}`}
              accessibilityHint="Opens the voice language selector"
              accessibilityState={{
                disabled: isSavingProfile,
                expanded: showVoiceLanguagePicker,
              }}
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
                accessibilityRole="button"
                accessibilityLabel="Cancel profile editing"
                accessibilityHint="Discards profile changes and closes the editor"
                accessibilityState={{
                  disabled: isSavingProfile,
                }}
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
                accessibilityRole="button"
                accessibilityLabel={
                  isSavingProfile
                    ? 'Saving profile'
                    : 'Save profile changes'
                }
                accessibilityHint="Saves your profile information"
                accessibilityState={{
                  disabled: isSavingProfile,
                  busy: isSavingProfile,
                }}
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
      </NIRACard>

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

        <NIRAButton
          title="Open WhatsApp Assistant"
          onPress={handleOpenWhatsApp}
          accessibilityHint="Opens the AI-assisted WhatsApp message screen"
          style={styles.whatsappButton}
        />
          <Text style={styles.communicationHint}>
            WhatsApp sending is not connected yet.
          </Text>
        
        <Text style={styles.communicationHint}>
          WhatsApp sending is not connected yet.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Phone Call Assistant
        </Text>

        <Text style={styles.communicationDescription}>
          Prepare AI-assisted responses for
          phone conversations.
        </Text>

        <NIRAButton
          title="Open Phone Call Assistant"
          onPress={handleOpenPhoneCall}
          accessibilityHint="Opens the AI-assisted phone call screen"
          style={styles.phoneCallButton}
        />
          <Text style={styles.communicationHint}>
            Phone calling is not connected yet.
          </Text>
      
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
          accessibilityLabel="Conversation title"
          accessibilityHint="Enter a title for the new conversation"
          value={conversationTitle}
          onChangeText={
            setConversationTitle
          }
          autoCapitalize="sentences"
          editable={
            !creatingConversation
          }
        />

        <NIRAButton
          title={
            creatingConversation
              ? 'Creating...'
              : 'New Conversation'
          }
          onPress={handleCreateConversation}
          disabled={creatingConversation}
          accessibilityHint="Creates a new conversation"
          style={styles.createButton}
        />
      </View>

      {/* NIRA PERSONAL PROFILE */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          NIRA Personal Profile
        </Text>

        <Text style={styles.cardText}>
          Personal information, communication preferences,
          instructions, privacy, and AI memory controls.
        </Text>

        <NIRAButton
          title="Open NIRA Profile"
          onPress={onOpenNIRAPersonalProfile}
          accessibilityHint="Opens your NIRA personal profile"
          style={styles.niraProfileButton}
        />
      </View>

      {/* CONVERSATIONS */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Conversations
        </Text>

        <TextInput
          style={styles.searchInput}
          placeholder="Search conversations..."
          accessibilityLabel="Search conversations"
          accessibilityHint="Enter text to search your conversations"
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
            accessibilityRole="tab"
            accessibilityLabel="Active conversations"
            accessibilityState={{
              selected: activeView === 'active',
            }}
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
                   accessible
                  accessibilityRole="button"
                  accessibilityLabel={`Conversation: ${
                    conversation.title || 'Untitled'
                  }`}
                  accessibilityHint={
                    activeView === 'trash'
                      ? 'This conversation is in Trash'
                      : 'Double tap to open. Long press for conversation actions.'
                  }
                  accessibilityState={{
                    disabled:
                      actionInProgress ||
                      !conversationId,
                    busy: actionInProgress,
                  }}
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
        <View 
          style={styles.inlineError}
          accessible
          accessibilityRole="alert"
          accessibilityLabel={`Error: ${error}`}
        >
          <Text
            style={styles.inlineErrorText}
          >
            {error}
          </Text>

          <Pressable
            onPress={
              refreshConversations
            }
            accessibilityRole="button"
            accessibilityLabel="Retry loading conversations"
            accessibilityHint="Attempts to load conversations again"
          >
            <Text
              style={styles.retryText}
            >
              Retry
            </Text>
          </Pressable>
        </View>
      ) : null}

      <NIRAButton
        title="Sign Out"
        onPress={handleLogout}
        accessibilityHint="Sign out of the current account"
        style={styles.logoutButton}
      />
    </NIRAScreen>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
    backgroundColor: '#f5f7fb',
  },

  container: {
    paddingHorizontal: 24,
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.xxxl,
  },

  center: {
    flex: 1,
    backgroundColor: '#f5f7fb',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },

  title: {
    fontSize: TYPOGRAPHY.heading,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginBottom: SPACING.xs,
  },

  subtitle: {
    fontSize: TYPOGRAPHY.small,
    color: COLORS.textSecondary,
    marginBottom: SPACING.lg,
  },

  card: {
    backgroundColor: COLORS.surface,
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: RADIUS.lg,
    padding: SPACING.xl,
    marginBottom: SPACING.lg,

    elevation: 2,
    shadowColor: COLORS.black,
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },

  cardTitle: {
    fontSize: TYPOGRAPHY.title,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginBottom: SPACING.sm,
  },
  
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SPACING.md,
  },

  editProfileButton: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.pill,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
  },

  editProfileButtonText: {
    color: COLORS.primary,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
  },

  cardText: {
    color: COLORS.text,
    fontSize: TYPOGRAPHY.body,
    lineHeight: 24,
    marginBottom: SPACING.sm,
  },

  niraProfileButton: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.md,
  },

  niraProfileButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
  },

  formLabel: {
    fontSize: TYPOGRAPHY.small,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },

 profileInput: {
  backgroundColor: COLORS.background,
  borderWidth: 1,
  borderColor: COLORS.border,
  borderRadius: RADIUS.md,
  paddingHorizontal: SPACING.lg,
  paddingVertical: SPACING.md,
  fontSize: TYPOGRAPHY.body,
  color: COLORS.text,
  marginBottom: SPACING.md,
},

  formHint: {
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
    marginBottom: SPACING.md,
  },

  languageSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },

  languageSelectorText: {
    color: COLORS.text,
    fontSize: TYPOGRAPHY.body,
    flex: 1,
  },

  languageSelectorArrow: {
    color: COLORS.primary,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
    marginLeft: SPACING.md,
  },

  languageOptions: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    marginBottom: SPACING.md,
    overflow: 'hidden',
  },

  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },

  languageOptionName: {
    color: COLORS.text,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
  },

  languageOptionNative: {
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.small,
    marginLeft: SPACING.sm,
  },

  profileActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: SPACING.md,
    marginTop: SPACING.lg,
  },

  cancelProfileButton: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
  },

  cancelProfileButtonText: {
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
  },

  saveProfileButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
  },

  saveProfileButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
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
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.lg,
    fontSize: TYPOGRAPHY.body,
    backgroundColor: COLORS.background,
    color: COLORS.text,
    marginBottom: SPACING.lg,
  },

  /*
   * WhatsApp Assistant styles.
   */
  communicationDescription: {
    fontSize: TYPOGRAPHY.small,
    lineHeight: 21,
    color: COLORS.textSecondary,
    marginBottom: SPACING.lg,
  },

  whatsappButton: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },

  whatsappButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
    textAlign: 'center',
  },

  phoneCallButton: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },

  phoneCallButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
    textAlign: 'center',
  },

  communicationHint: {
    marginTop: 9,
    fontSize: 12,
    lineHeight: 18,
    color: '#9ca3af',
    textAlign: 'center',
  },

  createButton: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.sm,
  },

 createButtonText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '700',
    textAlign: 'center',
  },

  buttonDisabled: {
    opacity: 0.5,
  },

 tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    borderRadius: RADIUS.md,
    padding: SPACING.xs,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  tab: {
    flex: 1,
    paddingVertical: SPACING.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: RADIUS.sm,
  },

  activeTab: {
    backgroundColor: COLORS.primary,
    elevation: 2,
  },

  tabText: {
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '600',
  },

  activeTabText: {
    color: COLORS.white,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
  },

  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },

  conversationContent: {
    flex: 1,
    justifyContent: 'center',
  },

  conversationTitle: {
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },

  conversationDate: {
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },

  actionHint: {
    fontSize: TYPOGRAPHY.caption,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },

  actionHelp: {
    fontSize: TYPOGRAPHY.small,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginTop: SPACING.sm,
  },

  itemDisabled: {
    opacity: 0.5,
  },

  listLoading: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xxl,
  },

  listLoadingText: {
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.small,
    marginTop: SPACING.md,
  },

  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xxxl,
    paddingHorizontal: SPACING.lg,
  },

 emptyStateTitle: {
    fontSize: TYPOGRAPHY.title,
    fontWeight: '700',
    color: COLORS.primaryDark,
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },

  emptyStateText: {
    fontSize: TYPOGRAPHY.small,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 21,
  },

  inlineError: {
    backgroundColor: '#FDECEC',
    borderWidth: 1,
    borderColor: COLORS.error,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
  },

  inlineErrorText: {
    color: COLORS.error,
    fontSize: TYPOGRAPHY.small,
    lineHeight: 20,
  },

  retryText: {
    color: COLORS.primary,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '700',
    marginTop: SPACING.sm,
  },

  loadingText: {
    color: COLORS.textSecondary,
    fontSize: TYPOGRAPHY.body,
    marginTop: SPACING.md,
    textAlign: 'center',
  },

  errorTitle: {
    fontSize: TYPOGRAPHY.heading,
    fontWeight: '700',
    color: COLORS.error,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },

  errorText: {
    fontSize: TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 23,
    marginBottom: SPACING.lg,
  },

  logoutButton: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.md,
  },

  logoutButtonText: {
    color: COLORS.text,
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
  },
});
