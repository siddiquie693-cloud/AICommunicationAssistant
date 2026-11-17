
import React from 'react';

import {
  View,
  Text,
  Pressable,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  TYPOGRAPHY,
} from './theme';

export default function NIRAHeader({
  title = 'NIRA AI',
  subtitle,
  onBack,
  rightAction,
}) {
  return (
    <View style={styles.container}>
      <View style={styles.left}>
        {onBack ? (
          <Pressable
            onPress={onBack}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={styles.backButton}
          >
            <Text style={styles.backText}>‹</Text>
          </Pressable>
        ) : null}

        <View style={styles.titleContainer}>
          <Text style={styles.title}>{title}</Text>

          {subtitle ? (
            <Text style={styles.subtitle}>
              {subtitle}
            </Text>
          ) : null}
        </View>
      </View>

      {rightAction || null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 64,
    paddingVertical: SPACING.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.background,
  },

  left: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },

  backButton: {
    paddingRight: SPACING.md,
    paddingVertical: SPACING.xs,
  },

  backText: {
    fontSize: 32,
    color: COLORS.primary,
  },

  titleContainer: {
    flex: 1,
  },

  title: {
    fontSize: TYPOGRAPHY.title,
    fontWeight: '700',
    color: COLORS.text,
  },

  subtitle: {
    marginTop: SPACING.xs,
    fontSize: TYPOGRAPHY.small,
    color: COLORS.textSecondary,
  },
});
