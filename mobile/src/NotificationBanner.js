import React, { useEffect } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

const NotificationBanner = ({
  visible,
  type = 'info',
  message = '',
  onDismiss,
  duration = 3000,
}) => {
  useEffect(() => {
    if (!visible || !message || !onDismiss) {
      return undefined;
    }

    const timer = setTimeout(() => {
      onDismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, [
    visible,
    message,
    onDismiss,
    duration,
  ]);

  if (!visible || !message) {
    return null;
  }

  return (
    <View
      style={[
        styles.container,
        type === 'success' &&
          styles.successContainer,
        type === 'error' &&
          styles.errorContainer,
      ]}
    >
      <Text style={styles.message}>
        {message}
      </Text>

      <Pressable
        onPress={onDismiss}
        accessibilityRole="button"
        accessibilityLabel="Dismiss notification"
      >
        <Text style={styles.dismiss}>
          ×
        </Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginHorizontal: 16,
    marginBottom: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#e8eef7',
  },

  successContainer: {
    backgroundColor: '#e8f5e9',
  },

  errorContainer: {
    backgroundColor: '#ffebee',
  },

  message: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    color: '#1f2937',
  },

  dismiss: {
    marginLeft: 12,
    fontSize: 22,
    lineHeight: 22,
    color: '#374151',
  },
});

export default NotificationBanner;