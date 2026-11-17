
import React from 'react';

import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  TYPOGRAPHY,
} from '../theme';

export default function NIRALoader({
  message = 'NIRA is thinking...',
  size = 'large',
}) {
  return (
    <View style={styles.container}>
      <ActivityIndicator
        size={size}
        color={COLORS.primary}
      />

      {message ? (
        <Text style={styles.message}>
          {message}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.lg,
  },

  message: {
    marginTop: SPACING.md,
    fontSize: TYPOGRAPHY.sm,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
});