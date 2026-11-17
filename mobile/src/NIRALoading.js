
import React from 'react';

import {
  View,
  Text,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  TYPOGRAPHY,
} from './theme';

export default function NIRALoading({
  message = 'Loading...',
  fullScreen = false,
}) {
  return (
    <View
      style={[
        styles.container,
        fullScreen && styles.fullScreen,
      ]}
      accessibilityRole="progressbar"
      accessibilityLabel={message}
    >
      <ActivityIndicator
        size="large"
        color={COLORS.primary}
      />

      <Text style={styles.message}>
        {message}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
  },

  fullScreen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  message: {
    marginTop: SPACING.md,
    fontSize: TYPOGRAPHY.small,
    color: COLORS.textSecondary,
  },
});
