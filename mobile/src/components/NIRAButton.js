
import React from 'react';

import {
  Pressable,
  Text,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from '../theme';

export default function NIRAButton({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
  accessibilityHint,
  accessibilityState,
}) {
  const isSecondary = variant === 'secondary';
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityHint={accessibilityHint}
      accessibilityState={{
        ...accessibilityState,
        disabled: isDisabled,
        busy: loading,
      }}
      style={({ pressed }) => [
        styles.button,
        isSecondary
          ? styles.secondary
          : styles.primary,
        style,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={
            isSecondary
              ? COLORS.primary
              : COLORS.white
          }
        />
      ) : (
        <Text
          style={[
            styles.text,
            isSecondary
              ? styles.secondaryText
              : styles.primaryText,
          ]}
        >
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.md,
    borderRadius: RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
  },

  primary: {
    backgroundColor: COLORS.primary,
  },

  secondary: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },

  text: {
    fontSize: TYPOGRAPHY.body,
    fontWeight: '600',
  },

  primaryText: {
    color: COLORS.white,
  },

  secondaryText: {
    color: COLORS.primary,
  },

  disabled: {
    opacity: 0.5,
  },

  pressed: {
    opacity: 0.8,
  },
});