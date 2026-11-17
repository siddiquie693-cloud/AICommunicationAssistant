
import React from 'react';

import {
  View,
  Text,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  TYPOGRAPHY,
} from '../theme';

export default function NIRAEmptyState({
  title = 'Nothing here yet',
  message = 'Your content will appear here.',
  style,
}) {
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>
        {title}
      </Text>

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

  title: {
    fontSize: TYPOGRAPHY.lg,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
  },

  message: {
    marginTop: SPACING.sm,
    fontSize: TYPOGRAPHY.sm,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
});