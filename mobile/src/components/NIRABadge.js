
import React from 'react';

import {
  View,
  Text,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from '../theme';

export default function NIRABadge({
  label,
  color = COLORS.accent,
  style,
}) {
  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: color + '20' },
        style,
      ]}
    >
      <Text
        style={[
          styles.label,
          { color },
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
    borderRadius: RADIUS.full,
  },

  label: {
    fontSize: TYPOGRAPHY.xs,
    fontWeight: '600',
  },
});