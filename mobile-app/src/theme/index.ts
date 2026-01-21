/**
 * SmartCrop Pakistan - Theme Constants
 */

export const colors = {
  // Primary
  primary: '#2E7D32',       // Green - agriculture theme
  primaryLight: '#4CAF50',
  primaryDark: '#1B5E20',
  
  // Secondary
  secondary: '#1976D2',     // Blue - technology/water
  secondaryLight: '#2196F3',
  
  // Status
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3',
  
  // Neutral
  white: '#FFFFFF',
  black: '#000000',
  background: '#F5F5F5',
  
  // Text
  textPrimary: '#212121',
  textSecondary: '#757575',
  textDisabled: '#BDBDBD',
  
  // Borders
  border: '#E0E0E0',
  divider: '#EEEEEE',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const typography = {
  sizes: {
    xs: 10,
    sm: 12,
    md: 14,
    lg: 18,
    xl: 24,
    xxl: 32,
  },
  weights: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

export const shadows = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  large: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
};
