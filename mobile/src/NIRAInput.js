
import React from 'react';

import {
  View,
  Text,
  TextInput,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
  RADIUS,
  TYPOGRAPHY,
} from './theme';

export default function NIRAInput({
  label,
  value,
  onChangeText,
  placeholder,
  secureTextEntry = false,
  keyboardType = 'default',
  multiline = false,
  error,
  style,
  editable = true,
  autoCapitalize = 'sentences',
  autoCorrect = true,
  accessibilityLabel,
  maxLength,
}) {
  return (
    <View style={[styles.container, style]}>
      {label ? (
        <Text style={styles.label}>{label}</Text>
      ) : null}

      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={COLORS.textSecondary}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        multiline={multiline}
        editable={editable}
        autoCapitalize={autoCapitalize}
        autoCorrect={autoCorrect}
        maxLength={maxLength}
        accessibilityLabel={accessibilityLabel || label || placeholder}
        accessibilityHint={error ? `Error: ${error}` : undefined}
        accessibilityState={{
          disabled: !editable,
        }}
        style={[
          styles.input,
          multiline && styles.multiline,
          !editable && styles.disabled,
          error && styles.inputError,
        ]}
      />

      {error ? (
        <Text
          style={styles.error}
          accessibilityRole="alert"
        >
          {error}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginBottom: SPACING.md,
  },

  label: {
    color: COLORS.text,
    fontSize: TYPOGRAPHY.small,
    fontWeight: '600',
    marginBottom: SPACING.sm,
  },

  input: {
    minHeight: 50,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    color: COLORS.text,
    fontSize: TYPOGRAPHY.body,
  },

  multiline: {
    minHeight: 110,
    textAlignVertical: 'top',
  },

  disabled: {
    opacity: 0.6,
  },

  inputError: {
    borderColor: COLORS.error,
  },

  error: {
    color: COLORS.error,
    fontSize: TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
  },
});