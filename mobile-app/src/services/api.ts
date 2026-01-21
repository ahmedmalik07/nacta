/**
 * SmartCrop Pakistan - API Client
 */

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://api.smartcrop.pk/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept-Language': 'ur',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token expiry
      await AsyncStorage.removeItem('auth_token');
      // Navigate to login
    }
    return Promise.reject(error);
  }
);

// API Methods
export const authAPI = {
  login: (phone: string, otp: string) => 
    apiClient.post('/auth/verify-otp', { phone, otp }),
  
  requestOTP: (phone: string) => 
    apiClient.post('/auth/request-otp', { phone }),
  
  logout: () => 
    apiClient.post('/auth/logout'),
};

export const farmsAPI = {
  getAll: () => apiClient.get('/farms/'),
  getById: (id: number) => apiClient.get(`/farms/${id}`),
  create: (data: any) => apiClient.post('/farms/', data),
  delete: (id: number) => apiClient.delete(`/farms/${id}`),
  getHealthSummary: (id: number) => apiClient.get(`/farms/${id}/health-summary`),
};

export const healthAPI = {
  analyze: (farmId: number, source: string = 'sentinel-2') =>
    apiClient.post('/health/analyze', { farm_id: farmId, source }),
  
  getHistory: (farmId: number, days: number = 30) =>
    apiClient.get(`/health/history/${farmId}?days=${days}`),
  
  detectDisease: (farmId: number, image: FormData) =>
    apiClient.post(`/health/detect-disease?farm_id=${farmId}`, image, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const predictionsAPI = {
  getYield: (farmId: number) =>
    apiClient.post('/predictions/predict', { farm_id: farmId }),
  
  getHistory: (farmId: number) =>
    apiClient.get(`/predictions/history/${farmId}`),
};

export const satelliteAPI = {
  fetch: (farmId: number) =>
    apiClient.post('/satellite/fetch', { farm_id: farmId }),
  
  getNDVITimeseries: (farmId: number, days: number = 90) =>
    apiClient.get(`/satellite/ndvi-timeseries/${farmId}?days=${days}`),
  
  getIndices: (farmId: number) =>
    apiClient.get(`/satellite/indices/${farmId}`),
};

export const agentAPI = {
  query: (message: string, language: string = 'ur', farmId?: number) =>
    apiClient.post('/agent/query', { message, language, farm_id: farmId }),
  
  voiceQuery: (audio: FormData, language: string = 'ur', farmId?: number) =>
    apiClient.post(`/agent/voice-query?language=${language}&farm_id=${farmId}`, audio, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  getHistory: (limit: number = 20) =>
    apiClient.get(`/agent/conversation-history?limit=${limit}`),
  
  submitFeedback: (conversationId: number, rating: number, text?: string) =>
    apiClient.post(`/agent/feedback/${conversationId}`, { rating, feedback_text: text }),
};
