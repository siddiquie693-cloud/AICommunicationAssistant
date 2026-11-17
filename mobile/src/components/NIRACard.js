
import React from 'react';

import {
  View,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  RADIUS,
} from '../theme';

export default function NIRACard({
  children,
  style,
}) {
  return (
    <View style={[styles.card, style]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
});
