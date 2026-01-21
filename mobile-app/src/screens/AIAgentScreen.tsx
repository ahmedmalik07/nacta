/**
 * SmartCrop Pakistan - AI Agent Screen
 * Voice and text-based conversational AI for farmers
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Voice from '@react-native-voice/voice';
import { useTranslation } from 'react-i18next';

import { colors, spacing, typography } from '../theme';
import { apiClient } from '../services/api';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  audioUrl?: string;
}

const suggestedQuestions = [
  'میری فصل کو کتنا پانی چاہیے؟',
  'گندم میں کون سی کھاد لگائیں؟',
  'کیڑوں سے بچاؤ کیسے کریں؟',
  'پیلے پتوں کا علاج کیا ہے؟',
];

const AIAgentScreen: React.FC = () => {
  const { t } = useTranslation();
  const scrollViewRef = useRef<ScrollView>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'السلام علیکم! میں آپ کا زرعی مشیر ہوں۔ آپ مجھ سے اردو، پنجابی یا سندھی میں سوال پوچھ سکتے ہیں۔ 🌾',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [partialText, setPartialText] = useState('');

  useEffect(() => {
    // Initialize voice recognition
    Voice.onSpeechStart = () => setIsRecording(true);
    Voice.onSpeechEnd = () => setIsRecording(false);
    Voice.onSpeechResults = (e) => {
      if (e.value && e.value[0]) {
        setInputText(e.value[0]);
        handleSend(e.value[0]);
      }
    };
    Voice.onSpeechPartialResults = (e) => {
      if (e.value && e.value[0]) {
        setPartialText(e.value[0]);
      }
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  useEffect(() => {
    if (isRecording) {
      // Pulse animation for recording indicator
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.3,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  const startRecording = async () => {
    try {
      await Voice.start('ur-PK'); // Urdu - Pakistan
      setPartialText('');
    } catch (error) {
      console.error('Voice error:', error);
    }
  };

  const stopRecording = async () => {
    try {
      await Voice.stop();
    } catch (error) {
      console.error('Voice stop error:', error);
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Call AI agent API
      const response = await apiClient.post('/agent/query', {
        message: messageText,
        language: 'ur',
        farm_id: null, // Could be selected farm
      });

      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response_text,
        isUser: false,
        timestamp: new Date(),
        audioUrl: response.data.response_audio_url,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      // Fallback response
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'معذرت، ابھی جواب نہیں مل سکا۔ براہ کرم دوبارہ کوشش کریں۔',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const handleSuggestedQuestion = (question: string) => {
    setInputText(question);
    handleSend(question);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="robot" size={32} color={colors.primary} />
        <View style={styles.headerText}>
          <Text style={styles.headerTitle}>🤖 AI زرعی مشیر</Text>
          <Text style={styles.headerSubtitle}>اردو • پنجابی • سندھی</Text>
        </View>
      </View>

      {/* Messages */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((message) => (
          <View
            key={message.id}
            style={[
              styles.messageBubble,
              message.isUser ? styles.userMessage : styles.aiMessage,
            ]}
          >
            {!message.isUser && (
              <Icon name="robot" size={20} color={colors.primary} style={styles.aiIcon} />
            )}
            <Text style={[
              styles.messageText,
              message.isUser && styles.userMessageText,
            ]}>
              {message.text}
            </Text>
            {message.audioUrl && (
              <TouchableOpacity style={styles.audioButton}>
                <Icon name="volume-high" size={20} color={colors.primary} />
              </TouchableOpacity>
            )}
          </View>
        ))}

        {isLoading && (
          <View style={[styles.messageBubble, styles.aiMessage]}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.typingText}>سوچ رہا ہوں...</Text>
          </View>
        )}

        {/* Partial speech text */}
        {isRecording && partialText && (
          <View style={styles.partialTextContainer}>
            <Text style={styles.partialText}>{partialText}</Text>
          </View>
        )}
      </ScrollView>

      {/* Suggested Questions */}
      {messages.length <= 2 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.suggestionsContainer}
          contentContainerStyle={styles.suggestionsContent}
        >
          {suggestedQuestions.map((question, index) => (
            <TouchableOpacity
              key={index}
              style={styles.suggestionChip}
              onPress={() => handleSuggestedQuestion(question)}
            >
              <Text style={styles.suggestionText}>{question}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Input Area */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.inputContainer}>
          {/* Voice Button */}
          <TouchableOpacity
            style={[styles.voiceButton, isRecording && styles.voiceButtonRecording]}
            onPressIn={startRecording}
            onPressOut={stopRecording}
          >
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <Icon
                name={isRecording ? 'microphone' : 'microphone-outline'}
                size={28}
                color={isRecording ? colors.white : colors.primary}
              />
            </Animated.View>
          </TouchableOpacity>

          {/* Text Input */}
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="یہاں لکھیں یا آواز سے بولیں..."
            placeholderTextColor={colors.textSecondary}
            multiline
            maxLength={500}
          />

          {/* Send Button */}
          <TouchableOpacity
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            onPress={() => handleSend()}
            disabled={!inputText.trim() || isLoading}
          >
            <Icon
              name="send"
              size={24}
              color={inputText.trim() ? colors.white : colors.textSecondary}
            />
          </TouchableOpacity>
        </View>

        {/* Recording Indicator */}
        {isRecording && (
          <View style={styles.recordingIndicator}>
            <View style={styles.recordingDot} />
            <Text style={styles.recordingText}>آواز ریکارڈ ہو رہی ہے... چھوڑنے پر بھیجیں</Text>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerText: {
    marginLeft: spacing.md,
  },
  headerTitle: {
    fontSize: typography.sizes.lg,
    fontWeight: 'bold',
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: typography.sizes.sm,
    color: colors.textSecondary,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: spacing.md,
  },
  messageBubble: {
    maxWidth: '85%',
    padding: spacing.md,
    borderRadius: 16,
    marginBottom: spacing.sm,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  userMessage: {
    backgroundColor: colors.primary,
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  aiMessage: {
    backgroundColor: colors.white,
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  aiIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  messageText: {
    fontSize: typography.sizes.md,
    color: colors.textPrimary,
    lineHeight: 24,
    flex: 1,
  },
  userMessageText: {
    color: colors.white,
  },
  audioButton: {
    marginLeft: spacing.sm,
    padding: spacing.xs,
  },
  typingText: {
    marginLeft: spacing.sm,
    color: colors.textSecondary,
    fontStyle: 'italic',
  },
  partialTextContainer: {
    backgroundColor: '#E3F2FD',
    padding: spacing.sm,
    borderRadius: 8,
    marginVertical: spacing.sm,
  },
  partialText: {
    color: colors.textSecondary,
    fontStyle: 'italic',
  },
  suggestionsContainer: {
    maxHeight: 50,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  suggestionsContent: {
    padding: spacing.sm,
  },
  suggestionChip: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    marginRight: spacing.sm,
  },
  suggestionText: {
    color: colors.primary,
    fontSize: typography.sizes.sm,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: spacing.md,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  voiceButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  voiceButtonRecording: {
    backgroundColor: colors.error,
  },
  textInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 100,
    backgroundColor: '#F5F5F5',
    borderRadius: 22,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.sizes.md,
    textAlign: 'right', // RTL for Urdu
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  sendButtonDisabled: {
    backgroundColor: '#E0E0E0',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.sm,
    backgroundColor: '#FFEBEE',
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.error,
    marginRight: spacing.sm,
  },
  recordingText: {
    color: colors.error,
    fontSize: typography.sizes.sm,
  },
});

export default AIAgentScreen;
