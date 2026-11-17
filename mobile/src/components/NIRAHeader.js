
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

export default function NIRAHeader({
  title = 'NIRA AI',
  subtitle,
  style,
}) {
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>
        {title}
      </Text>

      {subtitle ? (
        <Text style={styles.subtitle}>
          {subtitle}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: SPACING.md,
  },

  title: {
    fontSize: TYPOGRAPHY.xl,
    fontWeight: '700',
    color: COLORS.text,
  },

  subtitle: {
    marginTop: SPACING.xs,
    fontSize: TYPOGRAPHY.sm,
    color: COLORS.textSecondary,
  },
});