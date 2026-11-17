
import React from 'react';

import {
  View,
  ScrollView,
  StyleSheet,
} from 'react-native';

import {
  COLORS,
  SPACING,
} from './theme';

export default function NIRAScreen({
  children,
  scrollable = false,
  style,
  contentStyle,
  contentContainerStyle,
  keyboardShouldPersistTaps = 'handled',
  keyboardDismissMode,
  refreshControl,
}) {
  if (scrollable) {
    return (
      <ScrollView
        style={[styles.screen, style]}
        contentContainerStyle={[
          styles.content,
          contentStyle,
          contentContainerStyle,
        ]}
        keyboardShouldPersistTaps={keyboardShouldPersistTaps}
        keyboardDismissMode={keyboardDismissMode}
        refreshControl={refreshControl}
      >
        {children}
      </ScrollView>
    );
  }

  return (
    <View style={[styles.screen, styles.content, style]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SPACING.lg,
  },
});
