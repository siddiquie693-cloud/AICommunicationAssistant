import React from 'react';

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import NIRAPersonalProfileScreen from '../NIRAPersonalProfileScreen';

import {
  getNIRAPersonalProfile,
  getProfile,
  updateNIRAPersonalProfile,
  updateProfile,
} from '../profile';

import { getLanguages } from '../languages';

import { getAccessToken } from '../storage';

jest.mock('../profile', () => ({
  getProfile: jest.fn(),
  updateProfile: jest.fn(),
  getNIRAPersonalProfile: jest.fn(),
  updateNIRAPersonalProfile: jest.fn(),
}));

jest.mock('../languages', () => ({
  getLanguages: jest.fn(),
}));

jest.mock('../storage', () => ({
  getAccessToken: jest.fn(),
}));

const accountProfile = {
  id: 1,
  username: 'shahil',
  email: 'shahil@example.com',
  first_name: 'Shahil',
  last_name: 'Siddiquie',
  preferred_language: 'en',
  preferred_language_code: 'en',
  voice_language: 'en',
  voice_language_code: 'en',
  timezone: 'UTC',
};

const niraProfile = {
  id: 1,
  user: 1,
  languages: ['English'],
  communication_style: {},
  work_info: {},
  skills: [],
  interests: [],
  important_people: [],
  custom_instructions: '',
  privacy_settings: {},
  memory_settings: {},
};

const availableLanguages = [
  {
    code: 'en',
    name: 'English',
  },
  {
    code: 'hi',
    name: 'Hindi',
  },
  {
    code: 'ur',
    name: 'Urdu',
  },
];

function setupSuccessfulProfileLoad() {
  getAccessToken.mockResolvedValue(
    'test-access-token'
  );

  getProfile.mockResolvedValue(
    accountProfile
  );

  getNIRAPersonalProfile.mockResolvedValue(
    niraProfile
  );

  getLanguages.mockResolvedValue(
    availableLanguages
  );
}

describe('NIRAPersonalProfileScreen', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  test('renders the personal profile screen', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Personal Profile')
      ).toBeTruthy();
    });
  });

  test('renders personal information fields', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByDisplayValue('Shahil')
      ).toBeTruthy();

      expect(
        screen.getByDisplayValue('Siddiquie')
      ).toBeTruthy();

      expect(
        screen.getByDisplayValue('UTC')
      ).toBeTruthy();
    });
  });

  test('renders communication preferences section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          'Communication Preferences'
        )
      ).toBeTruthy();
    });
  });

  test('renders work information section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getAllByText('Work Information').length
      ).toBeGreaterThanOrEqual(2);
    });
  });

  test('renders custom instructions section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Custom Instructions')
      ).toBeTruthy();
    });
  });

  test('renders important people section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Important People')
      ).toBeTruthy();
    });
  });

  test('renders privacy settings section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Privacy Settings')
      ).toBeTruthy();
    });
  });

  test('renders AI memory settings section', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          'AI Memory Settings'
        )
      ).toBeTruthy();
    });
  });

  test('loads available languages for language selectors', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        getLanguages
      ).toHaveBeenCalled();
    });
  });

  test('opens preferred language picker', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText('Preferred Language')
      ).toBeTruthy();
    });

    const preferredLanguageButton =
      screen.getByLabelText(
        'Preferred Language: English'
      );

    await fireEvent.press(
      preferredLanguageButton
    );

    expect(
      screen.getAllByText(
        'Preferred Language'
      ).length
    ).toBeGreaterThanOrEqual(2);

    expect(
      screen.getByLabelText(
        'Select English'
      )
    ).toBeTruthy();
  });

  test('opens voice language picker', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getAllByText('Voice Language').length
      ).toBeGreaterThanOrEqual(1);
    });

    const voiceLanguageButton =
      screen.getByLabelText('Voice Language: English');

    await fireEvent.press(
      voiceLanguageButton
    );

    expect(
      screen.getAllByText(
        'Voice Language'
      ).length
    ).toBeGreaterThanOrEqual(2);

    expect(
      screen.getByLabelText(
        'Select English'
      )
    ).toBeTruthy();
  });

  test('allows editing first name', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const firstNameInput =
      await screen.findByDisplayValue(
        'Shahil'
      );

    await fireEvent.changeText(
      firstNameInput,
      'Ahmed'
    );

    expect(
      screen.getByDisplayValue('Ahmed')
    ).toBeTruthy();
  });

  test('allows editing last name', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const lastNameInput =
      await screen.findByDisplayValue(
        'Siddiquie'
      );

    await fireEvent.changeText(
      lastNameInput,
      'Khan'
    );

    expect(
      screen.getByDisplayValue('Khan')
    ).toBeTruthy();
  });

  test('allows editing timezone', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const timezoneInput =
      await screen.findByDisplayValue(
        'UTC'
      );

    await fireEvent.changeText(
      timezoneInput,
      'Asia/Kolkata'
    );

    expect(
      screen.getByDisplayValue(
        'Asia/Kolkata'
      )
    ).toBeTruthy();
  });

  test('allows editing additional languages', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const languagesInput =
      await screen.findByDisplayValue(
        'English'
      );

    await fireEvent.changeText(
      languagesInput,
      'English, Hindi, Urdu'
    );

    expect(
      screen.getByDisplayValue(
        'English, Hindi, Urdu'
      )
    ).toBeTruthy();
  });

  test('allows editing communication style JSON', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'Communication Style JSON'
      );

    await fireEvent.changeText(
      input,
      '{"tone":"professional"}'
    );

    expect(
      screen.getByDisplayValue(
        '{"tone":"professional"}'
      )
    ).toBeTruthy();
  });

  test('allows editing work information JSON', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'Work Information JSON'
      );

    await fireEvent.changeText(
      input,
      '{"role":"Backend Developer"}'
    );

    expect(
      screen.getByDisplayValue(
        '{"role":"Backend Developer"}'
      )
    ).toBeTruthy();
  });

  test('allows editing skills', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const blankInputs =
      screen.getAllByDisplayValue('');

    expect(
      blankInputs.length
    ).toBeGreaterThan(0);

    await fireEvent.changeText(
      blankInputs[0],
      'Python, Django, AI'
    );

    expect(
      screen.getByDisplayValue(
        'Python, Django, AI'
      )
    ).toBeTruthy();
  });

  test('allows editing interests', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const blankInputs =
      screen.getAllByDisplayValue('');

    expect(
      blankInputs.length
    ).toBeGreaterThan(1);

    await fireEvent.changeText(
      blankInputs[1],
      'AI, Technology, Research'
    );

    expect(
      screen.getByDisplayValue(
        'AI, Technology, Research'
      )
    ).toBeTruthy();
  });

  test('allows editing custom instructions', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const blankInputs =
      screen.getAllByDisplayValue('');

    expect(
      blankInputs.length
    ).toBeGreaterThan(2);

    await fireEvent.changeText(
      blankInputs[2],
      'Always ask before sending messages.'
    );

    expect(
      screen.getByDisplayValue(
        'Always ask before sending messages.'
      )
    ).toBeTruthy();
  });

  test('allows editing important people JSON', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'Important People JSON'
      );

    await fireEvent.changeText(
      input,
      '[{"name":"Family"}]'
    );

    expect(
      screen.getByDisplayValue(
        '[{"name":"Family"}]'
      )
    ).toBeTruthy();
  });

  test('allows editing privacy settings JSON', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'Privacy Settings JSON'
      );

    await fireEvent.changeText(
      input,
      '{"allow_cloud_ai":false}'
    );

    expect(
      screen.getByDisplayValue(
        '{"allow_cloud_ai":false}'
      )
    ).toBeTruthy();
  });

  test('allows editing AI memory settings JSON', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'AI Memory Settings JSON'
      );

    await fireEvent.changeText(
      input,
      '{"enabled":true}'
    );

    expect(
      screen.getByDisplayValue(
        '{"enabled":true}'
      )
    ).toBeTruthy();
  });

  test('saves account and NIRA profile updates together', async () => {
    setupSuccessfulProfileLoad();

    updateProfile.mockResolvedValue({
      ...accountProfile,
      first_name: 'Ahmed',
    });

    updateNIRAPersonalProfile.mockResolvedValue(
      niraProfile
    );

    await render(
      <NIRAPersonalProfileScreen />
    );

    const firstNameInput =
      await screen.findByDisplayValue(
        'Shahil'
      );

    await fireEvent.changeText(
      firstNameInput,
      'Ahmed'
    );

    await fireEvent.press(
      screen.getByText(
        'Save NIRA Profile'
      )
    );

    await waitFor(() => {
      expect(
        updateProfile
      ).toHaveBeenCalled();

      expect(
        updateNIRAPersonalProfile
      ).toHaveBeenCalled();
    });
  });

  test('does not submit invalid JSON profile fields', async () => {
    setupSuccessfulProfileLoad();

    await render(
      <NIRAPersonalProfileScreen />
    );

    const input =
      screen.getByLabelText(
        'Communication Style JSON'
      );

    await fireEvent.changeText(
      input,
      '{"invalid":'
    );

    await fireEvent.press(
      screen.getByText(
        'Save NIRA Profile'
      )
    );

    await waitFor(() => {
      expect(
        updateNIRAPersonalProfile
      ).not.toHaveBeenCalled();
    });
  });

  test('handles profile loading failure', async () => {
    getAccessToken.mockResolvedValue(
      'test-access-token'
    );

    getProfile.mockRejectedValue(
      new Error('Profile loading failed')
    );

    getNIRAPersonalProfile.mockRejectedValue(
      new Error('Profile loading failed')
    );

    getLanguages.mockRejectedValue(
      new Error('Languages loading failed')
    );

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          'Profile unavailable'
        )
      ).toBeTruthy();
    });
  });

  test('retries profile loading after an error', async () => {
    getAccessToken.mockResolvedValue(
      'test-access-token'
    );

    getProfile
      .mockRejectedValueOnce(
        new Error('Profile loading failed')
      )
      .mockResolvedValueOnce(
        accountProfile
      );

    getNIRAPersonalProfile
      .mockRejectedValueOnce(
        new Error('Profile loading failed')
      )
      .mockResolvedValueOnce(
        niraProfile
      );

    getLanguages
      .mockRejectedValueOnce(
        new Error('Languages loading failed')
      )
      .mockResolvedValueOnce(
        availableLanguages
      );

    await render(
      <NIRAPersonalProfileScreen />
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          'Profile unavailable'
        )
      ).toBeTruthy();
    });

    await fireEvent.press(
      screen.getByText('Try Again')
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          'Personal Profile'
        )
      ).toBeTruthy();
    });
  });
});