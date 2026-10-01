import React, {
  useEffect,
  useState,
} from 'react';

import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  getNIRAPersonalProfile,
  updateNIRAPersonalProfile,
  getProfile,
  updateProfile,
} from './profile';

import {
  getLanguages,
} from './languages';

import {
  getAccessToken,
} from './storage';


const NIRA_COLORS = {
  primary: '#6C5CE7',
  primaryDark: '#5145B8',
  primaryLight: '#EEEAFE',

  background: '#F7F7FC',
  card: '#FFFFFF',

  text: '#171724',
  secondaryText: '#68687A',
  mutedText: '#9191A2',
  border: '#E6E4F0',

  personal: '#6C5CE7',
  languages: '#3B82F6',
  communication: '#4F8CFF',
  work: '#F59E42',
  instructions: '#9B59E0',
  people: '#35B87A',
  privacy: '#27AE8A',
  memory: '#8E6CE8',

  error: '#D64545',
  success: '#2E9B63',
};


const SECTION_CONFIG = {
  personal: {
    accent: NIRA_COLORS.personal,
    icon: '◉',
  },
  languages: {
    accent: NIRA_COLORS.languages,
    icon: '文',
  },
  communication: {
    accent: NIRA_COLORS.communication,
    icon: '☷',
  },
  work: {
    accent: NIRA_COLORS.work,
    icon: '◆',
  },
  instructions: {
    accent: NIRA_COLORS.instructions,
    icon: '✦',
  },
  people: {
    accent: NIRA_COLORS.people,
    icon: '♙',
  },
  privacy: {
    accent: NIRA_COLORS.privacy,
    icon: '✓',
  },
  memory: {
    accent: NIRA_COLORS.memory,
    icon: '✧',
  },
};


const NIRAPersonalProfileScreen = ({
  onBack,
}) => {
  const [
    profile,
    setProfile,
  ] = useState(null);

  const [
    personalProfile,
    setPersonalProfile,
  ] = useState({
    first_name: '',
    last_name: '',
    preferred_language: '',
    voice_language: '',
    timezone: '',
  });

  const [
    availableLanguages,
    setAvailableLanguages,
  ] = useState([]);

  const [
    isLanguagePickerOpen,
    setIsLanguagePickerOpen,
  ] = useState(false);

  const [
    languagePickerType,
    setLanguagePickerType,
  ] = useState(null);

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isSaving,
    setIsSaving,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState('');

  const [
    jsonErrors,
    setJsonErrors,
  ] = useState({});

  const [
    jsonDrafts,
    setJsonDrafts,
  ] = useState({
    communication_style: '',
    work_info: '',
    important_people: '',
    privacy_settings: '',
    memory_settings: '',
  });


  const formatJson = (value) => {
    if (
      value === null ||
      value === undefined
    ) {
      return '';
    }

    try {
      return JSON.stringify(
        value,
        null,
        2
      );
    } catch (err) {
      return '';
    }
  };


  const parseJsonField = (
    value,
    fieldName
  ) => {
    try {
      const parsed = JSON.parse(value);

      setJsonErrors((current) => ({
        ...current,
        [fieldName]: '',
      }));

      return parsed;
    } catch (err) {
      setJsonErrors((current) => ({
        ...current,
        [fieldName]:
          'Enter valid JSON.',
      }));

      return null;
    }
  };


  const updateJsonDraft = (
    fieldName,
    value
  ) => {
    setJsonDrafts((current) => ({
      ...current,
      [fieldName]: value,
    }));

    if (
      jsonErrors[fieldName]
    ) {
      setJsonErrors((current) => ({
        ...current,
        [fieldName]: '',
      }));
    }
  };

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      setError('');
      setJsonErrors({});

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const [
        niraProfile,
        accountProfile,
        languages,
      ] = await Promise.all([
        getNIRAPersonalProfile(token),
        getProfile(token),
        getLanguages(),
      ]);

      setProfile(niraProfile);

      setAvailableLanguages(
        Array.isArray(languages)
          ? languages
          : []
      );

      setPersonalProfile({
        first_name:
          accountProfile.first_name || '',
        last_name:
          accountProfile.last_name || '',
        preferred_language:
          accountProfile.preferred_language || '',
        voice_language:
          accountProfile.voice_language || '',
        timezone:
          accountProfile.timezone || '',
      });

      setJsonDrafts({
        communication_style:
          formatJson(
            niraProfile.communication_style
          ),
        work_info:
          formatJson(
            niraProfile.work_info
          ),
        important_people:
          formatJson(
            niraProfile.important_people
          ),
        privacy_settings:
          formatJson(
            niraProfile.privacy_settings
          ),
        memory_settings:
          formatJson(
            niraProfile.memory_settings
          ),
      });
    } catch (err) {
      setError(
        err.message ||
        'Unable to load NIRA profile.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const openLanguagePicker = (
    type
  ) => {
    setLanguagePickerType(type);
    setIsLanguagePickerOpen(true);
  };

  const closeLanguagePicker = () => {
    setIsLanguagePickerOpen(false);
    setLanguagePickerType(null);
  };

  const selectLanguage = (
    languageCode
  ) => {
    if (
      languagePickerType ===
      'preferred'
    ) {
      setPersonalProfile(
        (current) => ({
          ...current,
          preferred_language:
            languageCode,
        })
      );
    }

    if (
      languagePickerType ===
      'voice'
    ) {
      setPersonalProfile(
        (current) => ({
          ...current,
          voice_language:
            languageCode,
        })
      );
    }

    closeLanguagePicker();
  };

  const getLanguageName = (
    languageCode
  ) => {
    return (
      availableLanguages.find(
        (language) =>
          language.code ===
          languageCode
      )?.name ||
      languageCode ||
      ''
    );
  };

  const updateProfileField = (
    field,
    value
  ) => {
    setProfile((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updatePersonalField = (
    field,
    value
  ) => {
    setPersonalProfile(
      (current) => ({
        ...current,
        [field]: value,
      })
    );
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError('');
      setJsonErrors({});

      const token = await getAccessToken();

      if (!token) {
        throw new Error(
          'Authentication token not found.'
        );
      }

      const updatedProfileData = {
        ...profile,
      };

      const jsonFields = [
        'communication_style',
        'work_info',
        'important_people',
        'privacy_settings',
        'memory_settings',
      ];

      for (
        const fieldName of jsonFields
      ) {
        const draftValue =
          jsonDrafts[fieldName];

        const parsedValue =
          parseJsonField(
            draftValue,
            fieldName
          );

        if (
          parsedValue === null
        ) {
          throw new Error(
            `${fieldName.replaceAll('_', ' ')} contains invalid JSON.`
          );
        }

        updatedProfileData[
          fieldName
        ] = parsedValue;
      }

      const [
        updatedNIRAProfile,
        updatedAccountProfile,
      ] = await Promise.all([
        updateNIRAPersonalProfile(
          token,
          updatedProfileData
        ),
        updateProfile(
          token,
          personalProfile
        ),
      ]);

      setProfile(
        updatedNIRAProfile
      );

      setPersonalProfile({
        first_name:
          updatedAccountProfile.first_name ||
          '',
        last_name:
          updatedAccountProfile.last_name ||
          '',
        preferred_language:
          updatedAccountProfile.preferred_language ||
          '',
        voice_language:
          updatedAccountProfile.voice_language ||
          '',
        timezone:
          updatedAccountProfile.timezone ||
          '',
      });

      setJsonDrafts({
        communication_style:
          formatJson(
            updatedNIRAProfile.communication_style
          ),
        work_info:
          formatJson(
            updatedNIRAProfile.work_info
          ),
        important_people:
          formatJson(
            updatedNIRAProfile.important_people
          ),
        privacy_settings:
          formatJson(
            updatedNIRAProfile.privacy_settings
          ),
        memory_settings:
          formatJson(
            updatedNIRAProfile.memory_settings
          ),
      });

      setJsonErrors({});

      Alert.alert(
        'Profile updated',
        'Your NIRA personal profile has been updated successfully.'
      );
    } catch (err) {
      setError(
        err.message ||
        'Unable to update NIRA profile.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingScreen}>
        <View
          style={styles.loadingIcon}
        >
          <Text
            style={
              styles.loadingIconText
            }
          >
            N
          </Text>
        </View>

        <ActivityIndicator
          size="large"
          color={NIRA_COLORS.primary}
        />

        <Text
          style={styles.statusText}
        >
          Loading your NIRA profile...
        </Text>

        <Text
          style={styles.statusSubtext}
        >
          Preparing your personal AI settings
        </Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.errorScreen}>
        <View
          style={styles.errorIcon}
        >
          <Text
            style={styles.errorIconText}
          >
            !
          </Text>
        </View>

        <Text
          style={styles.errorTitle}
        >
          Profile unavailable
        </Text>

        <Text
          style={styles.errorText}
        >
          {error ||
            'NIRA profile is unavailable.'}
        </Text>

        <TouchableOpacity
          style={styles.retryButton}
          onPress={loadProfile}
          accessibilityRole="button"
          accessibilityLabel="Retry loading NIRA profile"
        >
          <Text
            style={
              styles.retryButtonText
            }
          >
            Try Again
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={
        Platform.OS === 'ios'
          ? 'padding'
          : undefined
      }
    >
      <ScrollView
        contentContainerStyle={
          styles.container
        }
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* PROFILE HEADER */}

        <View
          style={styles.profileHeader}
        >
          <View
            style={styles.headerTopRow}
          >
            <TouchableOpacity
              style={styles.backButton}
              onPress={onBack}
              disabled={isSaving}
              accessibilityRole="button"
              accessibilityLabel="Back"
              accessibilityHint="Returns to the home screen"
            >
              <Text
                style={
                  styles.backButtonText
                }
              >
                ‹
              </Text>

              <Text
                style={
                  styles.backLabel
                }
              >
                Back
              </Text>
            </TouchableOpacity>

            <View
              style={styles.niraBadge}
            >
              <Text
                style={
                  styles.niraBadgeText
                }
              >
                NIRA
              </Text>
            </View>
          </View>

          <View
            style={styles.headerIdentity}
          >
            <View
              style={styles.profileAvatar}
            >
              <Text
                style={
                  styles.profileAvatarText
                }
              >
                N
              </Text>
            </View>

            <View
              style={styles.headerTextBlock}
            >
              <Text
                style={styles.title}
              >
                Personal Profile
              </Text>

              <Text
                style={styles.description}
              >
                Teach NIRA how to understand
                your preferences, communication,
                privacy, and personal context.
              </Text>
            </View>
          </View>

          <View
            style={styles.headerAccent}
          >
            <View
              style={
                styles.headerAccentPrimary
              }
            />

            <View
              style={
                styles.headerAccentSecondary
              }
            />

            <View
              style={
                styles.headerAccentTertiary
              }
            />
          </View>
        </View>


        {error ? (
          <View
            style={
              styles.errorContainer
            }
          >
            <View
              style={styles.errorDot}
            />

            <Text
              style={styles.errorText}
            >
              {error}
            </Text>
          </View>
        ) : null}

        {/* PERSONAL INFORMATION */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.personal.icon
            }
            accent={
              SECTION_CONFIG.personal.accent
            }
            title="Personal Information"
            description="Your basic account identity and language defaults."
          />

          <Text style={styles.label}>
            First Name
          </Text>

          <TextInput
            style={styles.input}
            value={
              personalProfile.first_name
            }
            onChangeText={(value) =>
              updatePersonalField(
                'first_name',
                value
              )
            }
            placeholder="Enter your first name"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />

          <Text style={styles.label}>
            Last Name
          </Text>

          <TextInput
            style={styles.input}
            value={
              personalProfile.last_name
            }
            onChangeText={(value) =>
              updatePersonalField(
                'last_name',
                value
              )
            }
            placeholder="Enter your last name"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />

          <Text style={styles.label}>
            Preferred Language
          </Text>

          <LanguageSelector
            value={
              personalProfile.preferred_language
                ? getLanguageName(
                    personalProfile.preferred_language
                  )
                : ''
            }
            placeholder="Select preferred language"
            onPress={() =>
              openLanguagePicker(
                'preferred'
              )
            }
            disabled={isSaving}
            accessibilityLabel="Preferred Language: English"
          />

          <Text style={styles.label}>
            Voice Language
          </Text>

          <LanguageSelector
            value={
              personalProfile.voice_language
                ? getLanguageName(
                    personalProfile.voice_language
                  )
                : ''
            }
            placeholder="Select voice language"
            onPress={() =>
              openLanguagePicker(
                'voice'
              )
            }
            disabled={isSaving}
            accessibilityLabel="Voice Language: English"
          />

          <Text style={styles.label}>
            Timezone
          </Text>

          <TextInput
            style={styles.input}
            value={
              personalProfile.timezone
            }
            onChangeText={(value) =>
              updatePersonalField(
                'timezone',
                value
              )
            }
            placeholder="e.g. Asia/Kolkata"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />
        </View>

        {/* LANGUAGES */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.languages.icon
            }
            accent={
              SECTION_CONFIG.languages.accent
            }
            title="Languages"
            description="Languages NIRA can associate with your personal profile."
          />

          <Text style={styles.label}>
            Additional Languages
          </Text>

          <TextInput
            style={styles.input}
            value={
              Array.isArray(
                profile.languages
              )
                ? profile.languages.join(
                    ', '
                  )
                : ''
            }
            onChangeText={(value) =>
              updateProfileField(
                'languages',
                value
                  .split(',')
                  .map(
                    (language) =>
                      language.trim()
                  )
                  .filter(Boolean)
              )
            }
            placeholder="English, Hindi, Urdu"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />

          <Text
            style={styles.helperText}
          >
            Separate multiple languages with commas.
          </Text>
        </View>

        {/* COMMUNICATION */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.communication.icon
            }
            accent={
              SECTION_CONFIG.communication.accent
            }
            title="Communication Preferences"
            description="Define how NIRA should communicate with you."
          />

          <Text style={styles.label}>
            Communication Style
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.jsonInput,
            ]}
            value={
              jsonDrafts.communication_style
            }
            accessibilityLabel="Communication Style JSON"

            onChangeText={(value) =>
              updateJsonDraft(
                'communication_style',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder={
              '{\n  "response_style": "clear",\n  "formality": "professional",\n  "response_length": "concise"\n}'
            }
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
            autoCapitalize="none"
            autoCorrect={false}
          />

          {jsonErrors.communication_style ? (
            <FieldError
              message={
                jsonErrors.communication_style
              }
            />
          ) : null}
        </View>

        {/* WORK */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.work.icon
            }
            accent={
              SECTION_CONFIG.work.accent
            }
            title="Work Information"
            description="Structured context about your professional life."
          />

          <Text style={styles.label}>
            Work Information
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.jsonInput,
            ]}
            value={
              jsonDrafts.work_info
            }

            accessibilityLabel="Work Information JSON"
            onChangeText={(value) =>
              updateJsonDraft(
                'work_info',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder={
              '{\n  "role": "Software Engineer",\n  "company": "Example"\n}'
            }
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
            autoCapitalize="none"
            autoCorrect={false}
          />

          {jsonErrors.work_info ? (
            <FieldError
              message={
                jsonErrors.work_info
              }
            />
          ) : null}


          <Text style={styles.label}>
            Skills
          </Text>

          <TextInput
            style={styles.input}
            value={
              Array.isArray(
                profile.skills
              )
                ? profile.skills.join(
                    ', '
                  )
                : ''
            }
            onChangeText={(value) =>
              updateProfileField(
                'skills',
                value
                  .split(',')
                  .map(
                    (skill) =>
                      skill.trim()
                  )
                  .filter(Boolean)
              )
            }
            placeholder="Python, Django, AI, SQL"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />

          <Text
            style={styles.helperText}
          >
            Separate skills with commas.
          </Text>

          <Text style={styles.label}>
            Interests
          </Text>

          <TextInput
            style={styles.input}
            value={
              Array.isArray(
                profile.interests
              )
                ? profile.interests.join(
                    ', '
                  )
                : ''
            }
            onChangeText={(value) =>
              updateProfileField(
                'interests',
                value
                  .split(',')
                  .map(
                    (interest) =>
                      interest.trim()
                  )
                  .filter(Boolean)
              )
            }
            placeholder="AI, technology, reading"
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />

          <Text
            style={styles.helperText}
          >
            Separate interests with commas.
          </Text>
        </View>


        {/* CUSTOM INSTRUCTIONS */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.instructions.icon
            }
            accent={
              SECTION_CONFIG.instructions.accent
            }
            title="Custom Instructions"
            description="Rules that guide NIRA's behavior for you."
          />

          <Text style={styles.label}>
            Instructions
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.multilineInput,
            ]}
            value={
              profile.custom_instructions ||
              ''
            }
            onChangeText={(value) =>
              updateProfileField(
                'custom_instructions',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder="Example: Always ask before sending a message."
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
          />
        </View>


        {/* IMPORTANT PEOPLE */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.people.icon
            }
            accent={
              SECTION_CONFIG.people.accent
            }
            title="Important People"
            description="References to people who matter in your personal context."
          />

          <Text style={styles.label}>
            People
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.jsonInput,
            ]}
            value={
              jsonDrafts.important_people
            }

            accessibilityLabel="Important People JSON"
            onChangeText={(value) =>
              updateJsonDraft(
                'important_people',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder={
              '[\n  {"name": "Person", "relationship": "friend"}\n]'
            }
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
            autoCapitalize="none"
            autoCorrect={false}
          />

          {jsonErrors.important_people ? (
            <FieldError
              message={
                jsonErrors.important_people
              }
            />
          ) : null}
        </View>


        {/* PRIVACY */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.privacy.icon
            }
            accent={
              SECTION_CONFIG.privacy.accent
            }
            title="Privacy Settings"
            description="Control how NIRA may use personal profile information."
          />

          <View
            style={styles.securityNotice}
          >
            <View
              style={[
                styles.noticeIcon,
                {
                  backgroundColor:
                    NIRA_COLORS.privacy +
                    '18',
                },
              ]}
            >
              <Text
                style={[
                  styles.noticeIconText,
                  {
                    color:
                      NIRA_COLORS.privacy,
                  },
                ]}
              >
                ✓
              </Text>
            </View>

            <Text
              style={styles.noticeText}
            >
              These settings control NIRA's profile behavior. Android permissions remain separate.
            </Text>
          </View>

          <Text style={styles.label}>
            Privacy Configuration
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.jsonInput,
            ]}
            value={
              jsonDrafts.privacy_settings
            }

            accessibilityLabel="Privacy Settings JSON"
            onChangeText={(value) =>
              updateJsonDraft(
                'privacy_settings',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder={
              '{\n  "allow_ai_usage": true,\n  "allow_cloud_ai": false,\n  "allow_sensitive_info": false\n}'
            }
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
            autoCapitalize="none"
            autoCorrect={false}
          />

          {jsonErrors.privacy_settings ? (
            <FieldError
              message={
                jsonErrors.privacy_settings
              }
            />
          ) : null}
        </View>

        {/* MEMORY */}

        <View
          style={styles.sectionCard}
        >
          <SectionHeader
            icon={
              SECTION_CONFIG.memory.icon
            }
            accent={
              SECTION_CONFIG.memory.accent
            }
            title="AI Memory Settings"
            description="Control how NIRA's future memory system should use personal information."
          />

          <View
            style={[
              styles.memoryBanner,
              {
                backgroundColor:
                  NIRA_COLORS.memory +
                  '12',
              },
            ]}
          >
            <View
              style={[
                styles.memoryIcon,
                {
                  backgroundColor:
                    NIRA_COLORS.memory +
                    '20',
                },
              ]}
            >
              <Text
                style={[
                  styles.memoryIconText,
                  {
                    color:
                      NIRA_COLORS.memory,
                  },
                ]}
              >
                ✦
              </Text>
            </View>

            <View
              style={styles.memoryBannerText}
            >
              <Text
                style={styles.memoryBannerTitle}
              >
                Personal AI Memory
              </Text>

              <Text
                style={styles.memoryBannerDescription}
              >
                Your settings stay user-controlled.
                The actual Memory Engine is implemented later in Phase 3.
              </Text>
            </View>
          </View>

          <Text style={styles.label}>
            Memory Configuration
          </Text>

          <TextInput
            style={[
              styles.input,
              styles.jsonInput,
            ]}
            value={
              jsonDrafts.memory_settings
            }

            accessibilityLabel="AI Memory Settings JSON"
            onChangeText={(value) =>
              updateJsonDraft(
                'memory_settings',
                value
              )
            }
            multiline
            textAlignVertical="top"
            placeholder={
              '{\n  "allow_memory": true,\n  "allow_personal_memory": true\n}'
            }
            placeholderTextColor={
              NIRA_COLORS.mutedText
            }
            editable={!isSaving}
            autoCapitalize="none"
            autoCorrect={false}
          />

          {jsonErrors.memory_settings ? (
            <FieldError
              message={
                jsonErrors.memory_settings
              }
            />
          ) : null}
        </View>

        {/* SAVE */}

        <TouchableOpacity
          style={[
            styles.saveButton,
            isSaving &&
              styles.disabledButton,
          ]}
          onPress={handleSave}
          disabled={isSaving}
          accessibilityRole="button"
          accessibilityLabel="Save NIRA personal profile"
          accessibilityHint="Saves account and NIRA personalization settings"
        >
          {isSaving ? (
            <>
              <ActivityIndicator
                color="#FFFFFF"
                size="small"
              />

              <Text
                style={
                  styles.saveButtonText
                }
              >
                Saving Profile...
              </Text>
            </>
          ) : (
            <>
              <Text
                style={
                  styles.saveButtonIcon
                }
              >
                ✓
              </Text>

              <Text
                style={
                  styles.saveButtonText
                }
              >
                Save NIRA Profile
              </Text>
            </>
          )}
        </TouchableOpacity>

        <View
          style={styles.bottomNoteContainer}
        >
          <Text
            style={styles.bottomNote}
          >
            Your account information and NIRA
            personalization settings are saved
            together.
          </Text>
        </View>
      </ScrollView>


      {/* LANGUAGE PICKER */}

      <Modal
        visible={
          isLanguagePickerOpen
        }
        transparent
        animationType="slide"
        onRequestClose={
          closeLanguagePicker
        }
      >
        <View
          style={
            styles.modalOverlay
          }
        >
          <View
            style={
              styles.languagePicker
            }
          >
            <View
              style={
                styles.modalHandle
              }
            />

            <View
              style={
                styles.modalHeader
              }
            >
              <View>
                <Text
                  style={
                    styles.modalEyebrow
                  }
                >
                  NIRA LANGUAGE
                </Text>

                <Text
                  style={
                    styles.modalTitle
                  }
                >
                  {languagePickerType ===
                  'voice'
                    ? 'Voice Language'
                    : 'Preferred Language'}
                </Text>
              </View>

              <TouchableOpacity
                style={
                  styles.modalCloseButton
                }
                onPress={
                  closeLanguagePicker
                }
                accessibilityRole="button"
                accessibilityLabel="Close language picker"
              >
                <Text
                  style={
                    styles.modalCloseText
                  }
                >
                  ×
                </Text>
              </TouchableOpacity>
            </View>

            <Text
              style={
                styles.modalDescription
              }
            >
              Choose one of the languages available to your NIRA profile.
            </Text>


            <ScrollView
              style={
                styles.languageList
              }
              showsVerticalScrollIndicator={false}
            >
              {availableLanguages.length ===
              0 ? (
                <View
                  style={
                    styles.emptyLanguageState
                  }
                >
                  <Text
                    style={
                      styles.emptyLanguageText
                    }
                  >
                    No languages are currently available.
                  </Text>
                </View>
              ) : (
                availableLanguages.map(
                  (language) => {
                    const isSelected =
                      (
                        languagePickerType ===
                        'preferred'
                          ? personalProfile.preferred_language
                          : personalProfile.voice_language
                      ) ===
                      language.code;

                    return (
                      <TouchableOpacity
                        key={language.id || language.code}
                        style={[
                          styles.languageOption,
                          isSelected &&
                            styles.languageOptionSelected,
                        ]}
                        onPress={() =>
                          selectLanguage(
                            language.code
                          )
                        }
                        disabled={isSaving}
                        accessibilityRole="button"
                        accessibilityLabel={`Select ${language.name}`}
                      >
                        <View
                          style={
                            styles.languageOptionIcon
                          }
                        >
                          <Text
                            style={
                              styles.languageOptionIconText
                            }
                          >
                            {language.name
                              .charAt(0)
                              .toUpperCase()}
                          </Text>
                        </View>

                        <View
                          style={
                            styles.languageOptionContent
                          }
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
                              styles.languageNativeName
                            }
                          >
                            {
                              language.native_name
                            }
                          </Text>
                        </View>

                        <View
                          style={
                            styles.languageOptionRight
                          }
                        >
                          <Text
                            style={
                              styles.languageCode
                            }
                          >
                            {
                              language.code.toUpperCase()
                            }
                          </Text>

                          {isSelected ? (
                            <View
                              style={
                                styles.selectedCheck
                              }
                            >
                              <Text
                                style={
                                  styles.selectedCheckText
                                }
                              >
                                ✓
                              </Text>
                            </View>
                          ) : null}
                        </View>
                      </TouchableOpacity>
                    );
                  }
                )
              )}
            </ScrollView>


            <TouchableOpacity
              style={
                styles.cancelButton
              }
              onPress={
                closeLanguagePicker
              }
              accessibilityRole="button"
              accessibilityLabel="Cancel language selection"
            >
              <Text
                style={
                  styles.cancelButtonText
                }
              >
                Cancel
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
};


const SectionHeader = ({
  icon,
  accent,
  title,
  description,
}) => {
  return (
    <View
      style={styles.sectionHeader}
    >
      <View
        style={[
          styles.sectionIcon,
          {
            backgroundColor:
              accent + '18',
          },
        ]}
      >
        <Text
          style={[
            styles.sectionIconText,
            {
              color: accent,
            },
          ]}
        >
          {icon}
        </Text>
      </View>

      <View
        style={styles.sectionHeaderText}
      >
        <Text
          style={styles.sectionTitle}
        >
          {title}
        </Text>

        <Text
          style={styles.sectionDescription}
        >
          {description}
        </Text>
      </View>
    </View>
  );
};


const LanguageSelector = ({
  value,
  placeholder,
  onPress,
  disabled,
  accessibilityLabel,
}) => {
  return (
    <TouchableOpacity
      style={[
        styles.selectInput,
        disabled &&
          styles.selectDisabled,
      ]}
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || value || placeholder}
    >
      <View
        style={styles.selectContent}
      >
        <View
          style={[
            styles.selectDot,
            {
              backgroundColor: value
                ? NIRA_COLORS.primary
                : NIRA_COLORS.border,
            },
          ]}
        />

        <Text
          style={
            value
              ? styles.selectText
              : styles.placeholderText
          }
        >
          {value || placeholder}
        </Text>
      </View>

      <Text
        style={styles.selectArrow}
      >
        ›
      </Text>
    </TouchableOpacity>
  );
}; 


const FieldError = ({
  message,
}) => {
  return (
    <Text
      style={
        styles.fieldErrorText
      }
    >
      {message}
    </Text>
  );
};


const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor:
      NIRA_COLORS.background,
  },

  container: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 50,
  },

  /* HEADER */

  profileHeader: {
    marginBottom: 8,
    paddingHorizontal: 4,
    paddingTop: 2,
  },

  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 22,
  },

  backButton: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 10,
  },

  backButtonText: {
    fontSize: 32,
    lineHeight: 34,
    fontWeight: '300',
    color: NIRA_COLORS.text,
    marginRight: 4,
  },

  backLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: NIRA_COLORS.secondaryText,
  },

  niraBadge: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor:
      NIRA_COLORS.primaryLight,
  },

  niraBadgeText: {
    color: NIRA_COLORS.primaryDark,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
  },

  headerIdentity: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  profileAvatar: {
    width: 58,
    height: 58,
    borderRadius: 18,
    backgroundColor:
      NIRA_COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },

  profileAvatarText: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '800',
  },

  headerTextBlock: {
    flex: 1,
    minWidth: 0,
  },

  title: {
    fontSize: 27,
    lineHeight: 33,
    fontWeight: '800',
    color: NIRA_COLORS.text,
    marginBottom: 6,
  },

  description: {
    fontSize: 14,
    lineHeight: 20,
    color: NIRA_COLORS.secondaryText,
  },

  headerAccent: {
    height: 5,
    flexDirection: 'row',
    marginTop: 22,
    borderRadius: 5,
    overflow: 'hidden',
  },

  headerAccentPrimary: {
    flex: 5,
    backgroundColor:
      NIRA_COLORS.primary,
  },

  headerAccentSecondary: {
    flex: 2,
    backgroundColor:
      NIRA_COLORS.communication,
  },

  headerAccentTertiary: {
    flex: 1,
    backgroundColor:
      NIRA_COLORS.memory,
  },

  /* SECTION CARDS */

  sectionCard: {
    backgroundColor:
      NIRA_COLORS.card,
    borderRadius: 18,
    padding: 17,
    marginTop: 16,
    borderWidth: 1,
    borderColor:
      NIRA_COLORS.border,
  },

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 5,
  },

  sectionIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  sectionIconText: {
    fontSize: 19,
    fontWeight: '800',
  },

  sectionHeaderText: {
    flex: 1,
    minWidth: 0,
  },

  sectionTitle: {
    fontSize: 18,
    lineHeight: 23,
    fontWeight: '800',
    color: NIRA_COLORS.text,
  },

  sectionDescription: {
    marginTop: 3,
    fontSize: 13,
    lineHeight: 18,
    color: NIRA_COLORS.secondaryText,
  },

  /* INPUTS */

  label: {
    fontSize: 14,
    fontWeight: '700',
    color: NIRA_COLORS.text,
    marginTop: 17,
    marginBottom: 8,
  },

  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor:
      NIRA_COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    lineHeight: 21,
    backgroundColor:
      NIRA_COLORS.background,
    color: NIRA_COLORS.text,
  },

  selectInput: {
    minHeight: 50,
    borderWidth: 1,
    borderColor:
      NIRA_COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    backgroundColor:
      NIRA_COLORS.background,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  selectDisabled: {
    opacity: 0.6,
  },

  selectContent: {
    flex: 1,
    minWidth: 0,
    flexDirection: 'row',
    alignItems: 'center',
  },

  selectDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 10,
  },

  selectText: {
    flex: 1,
    fontSize: 16,
    color: NIRA_COLORS.text,
  },

  placeholderText: {
    flex: 1,
    fontSize: 16,
    color: NIRA_COLORS.mutedText,
  },

  selectArrow: {
    fontSize: 27,
    lineHeight: 27,
    color: NIRA_COLORS.secondaryText,
    marginLeft: 10,
  },

  multilineInput: {
    minHeight: 145,
  },

  jsonInput: {
    minHeight: 165,
    fontFamily:
      Platform.OS === 'ios'
        ? 'Menlo'
        : 'monospace',
    textAlignVertical: 'top',
  },

  helperText: {
    marginTop: 7,
    fontSize: 12,
    lineHeight: 18,
    color: NIRA_COLORS.mutedText,
  },

  /* PRIVACY / MEMORY */

  securityNotice: {
    marginTop: 14,
    padding: 12,
    borderRadius: 12,
    backgroundColor:
      NIRA_COLORS.privacy + '0D',
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  noticeIcon: {
    width: 30,
    height: 30,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  noticeIconText: {
    fontSize: 15,
    fontWeight: '800',
  },

  noticeText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
    color: NIRA_COLORS.secondaryText,
  },

  memoryBanner: {
    marginTop: 14,
    borderRadius: 14,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  memoryIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  memoryIconText: {
    fontSize: 18,
    fontWeight: '800',
  },

  memoryBannerText: {
    flex: 1,
    minWidth: 0,
  },

  memoryBannerTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: NIRA_COLORS.text,
    marginBottom: 3,
  },

  memoryBannerDescription: {
    fontSize: 12,
    lineHeight: 18,
    color: NIRA_COLORS.secondaryText,
  },

  /* ERRORS */

  errorContainer: {
    marginTop: 14,
    padding: 12,
    borderRadius: 12,
    backgroundColor:
      NIRA_COLORS.error + '0D',
    borderWidth: 1,
    borderColor:
      NIRA_COLORS.error + '25',
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  errorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor:
      NIRA_COLORS.error,
    marginTop: 6,
    marginRight: 9,
  },

  errorText: {
    flex: 1,
    color: NIRA_COLORS.error,
    fontSize: 13,
    lineHeight: 19,
  },

  fieldErrorText: {
    color: NIRA_COLORS.error,
    marginTop: 7,
    fontSize: 12,
    lineHeight: 17,
  },

  /* SAVE */

  saveButton: {
    marginTop: 22,
    minHeight: 54,
    borderRadius: 15,
    backgroundColor:
      NIRA_COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 20,
  },

  disabledButton: {
    opacity: 0.65,
  },

  saveButtonIcon: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
    marginRight: 8,
  },

  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },

  bottomNoteContainer: {
    paddingHorizontal: 12,
    paddingTop: 12,
  },

  bottomNote: {
    textAlign: 'center',
    color: NIRA_COLORS.mutedText,
    fontSize: 12,
    lineHeight: 18,
  },

  /* LOADING */

  loadingScreen: {
    flex: 1,
    backgroundColor:
      NIRA_COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },

  loadingIcon: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor:
      NIRA_COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 22,
  },

  loadingIconText: {
    color: '#FFFFFF',
    fontSize: 30,
    fontWeight: '800',
  },

  statusText: {
    marginTop: 14,
    fontSize: 16,
    fontWeight: '700',
    color: NIRA_COLORS.text,
  },

  statusSubtext: {
    marginTop: 5,
    fontSize: 13,
    color: NIRA_COLORS.secondaryText,
    textAlign: 'center',
  },

  /* ERROR SCREEN */

  errorScreen: {
    flex: 1,
    backgroundColor:
      NIRA_COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },

  errorIcon: {
    width: 58,
    height: 58,
    borderRadius: 18,
    backgroundColor:
      NIRA_COLORS.error + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 15,
  },

  errorIconText: {
    color: NIRA_COLORS.error,
    fontSize: 25,
    fontWeight: '800',
  },

  errorTitle: {
    fontSize: 21,
    fontWeight: '800',
    color: NIRA_COLORS.text,
    marginBottom: 8,
  },

  retryButton: {
    marginTop: 18,
    minHeight: 48,
    paddingHorizontal: 26,
    paddingVertical: 13,
    borderRadius: 12,
    backgroundColor:
      NIRA_COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },

  /* MODAL */

  modalOverlay: {
    flex: 1,
    backgroundColor:
      'rgba(15, 15, 25, 0.48)',
    justifyContent: 'flex-end',
  },

  languagePicker: {
    backgroundColor:
      NIRA_COLORS.card,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 18,
    paddingTop: 9,
    paddingBottom: 20,
    maxHeight: '84%',
  },

  modalHandle: {
    width: 42,
    height: 4,
    borderRadius: 4,
    alignSelf: 'center',
    backgroundColor:
      NIRA_COLORS.border,
    marginBottom: 15,
  },

  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  modalEyebrow: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
    color:
      NIRA_COLORS.primary,
    marginBottom: 3,
  },

  modalTitle: {
    fontSize: 21,
    fontWeight: '800',
    color: NIRA_COLORS.text,
  },

  modalCloseButton: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor:
      NIRA_COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },

  modalCloseText: {
    fontSize: 27,
    lineHeight: 28,
    color: NIRA_COLORS.secondaryText,
    fontWeight: '300',
  },

  modalDescription: {
    marginTop: 6,
    marginBottom: 12,
    fontSize: 13,
    lineHeight: 19,
    color: NIRA_COLORS.secondaryText,
  },

  languageList: {
    marginBottom: 10,
  },

  languageOption: {
    minHeight: 68,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },

  languageOptionSelected: {
    backgroundColor:
      NIRA_COLORS.primaryLight,
  },

  languageOptionIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor:
      NIRA_COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  languageOptionIconText: {
    fontSize: 17,
    fontWeight: '800',
    color:
      NIRA_COLORS.primaryDark,
  },

  languageOptionContent: {
    flex: 1,
    minWidth: 0,
  },

  languageOptionName: {
    fontSize: 15,
    fontWeight: '700',
    color: NIRA_COLORS.text,
  },

  languageNativeName: {
    marginTop: 3,
    fontSize: 12,
    color: NIRA_COLORS.secondaryText,
  },

  languageOptionRight: {
    alignItems: 'flex-end',
    justifyContent: 'center',
    marginLeft: 8,
  },

  languageCode: {
    fontSize: 11,
    fontWeight: '700',
    color: NIRA_COLORS.mutedText,
    letterSpacing: 0.5,
  },

  selectedCheck: {
    width: 22,
    height: 22,
    borderRadius: 7,
    backgroundColor:
      NIRA_COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },

  selectedCheckText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },

  emptyLanguageState: {
    paddingVertical: 30,
    alignItems: 'center',
  },

  emptyLanguageText: {
    color: NIRA_COLORS.secondaryText,
    fontSize: 14,
    textAlign: 'center',
  },

  cancelButton: {
    minHeight: 48,
    marginTop: 4,
    borderRadius: 13,
    backgroundColor:
      NIRA_COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },

  cancelButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: NIRA_COLORS.text,
  },
});


export default NIRAPersonalProfileScreen;