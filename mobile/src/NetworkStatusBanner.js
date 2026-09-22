import React from 'react';

import {
  StyleSheet,
  Text,
  View,
} from 'react-native';

const NetworkStatusBanner = ({
  isOffline,
}) => {
  if (!isOffline) {
    return null;
  }

  return (
    <View
      style={styles.container}
      accessibilityRole="alert"
      accessibilityLabel="No internet connection"
    >
      <Text style={styles.title}>
        No internet connection
      </Text>

      <Text style={styles.message}>
        Check your network connection.
        The app will reconnect automatically
        when internet access is restored.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#ffebee',
    borderWidth: 1,
    borderColor: '#f0c8c8',
  },

  title: {
    fontSize: 14,
    fontWeight: '700',
    color: '#b71c1c',
    marginBottom: 4,
  },

  message: {
    fontSize: 13,
    lineHeight: 18,
    color: '#7f1d1d',
  },
});

export default NetworkStatusBanner;