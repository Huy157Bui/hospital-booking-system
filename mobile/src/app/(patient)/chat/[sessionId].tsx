import React, { useState, useEffect, useRef } from 'react';
import { 
  View, Text, StyleSheet, TextInput, TouchableOpacity, 
  FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
  LayoutAnimation
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context'; 
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { chatService } from '../../../services/chatService';
import { ChatMessage } from '../../../types/chat';

interface ExtendedChatMessage extends ChatMessage {
  suggestions?: string[];
}

const formatTime = (dateString: string) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
};

export default function ChatDetailScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);

  const [messages, setMessages] = useState<ExtendedChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadMessages();
  }, [sessionId]);

  const loadMessages = async () => {
    try {
      const data = await chatService.getMessages(Number(sessionId));
      setMessages(data.map((msg: any) => ({ ...msg, suggestions: msg.suggestions || [] })));
      scrollToBottom();
    } catch (error) {
      console.error('Lỗi tải tin nhắn:', error);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText.trim();
    if (!text || isLoading) return;

    setInputText('');
    
    const tempUserMsgId = Date.now();
    const newUserMsg = { 
      id: tempUserMsgId, 
      session_id: Number(sessionId), 
      role: 'user' as const, 
      content: text, 
      created_date: new Date().toISOString() 
    };
    
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);
    scrollToBottom();

    try {
      const response: any = await chatService.sendMessage(Number(sessionId), text);
      
      const aiMsgFromBackend = response.assistant_message || { 
        id: Date.now() + 1, 
        session_id: Number(sessionId),
        role: 'assistant' as const, 
        content: 'Xin lỗi, tôi không thể phản hồi lúc này.', 
        created_date: new Date().toISOString() 
      };
      
      const finalAiMsg = {
        ...aiMsgFromBackend,
        suggestions: response.suggestions || []
      };

      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setMessages(prev => [...prev, finalAiMsg]);
    } catch (error: any) {
      console.error('Lỗi gửi tin nhắn:', error);
      Alert.alert('Lỗi', 'Không thể gửi tin nhắn. Vui lòng thử lại.');
      
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setMessages(prev => prev.filter(msg => msg.id !== tempUserMsgId));
      setInputText(text);
    } finally {
      setIsLoading(false);
      scrollToBottom();
    }
  };

  const renderMessage = ({ item }: { item: ExtendedChatMessage }) => {
    const isUser = item.role === 'user';

    return (
      <View style={[styles.messageRow, isUser ? styles.userRow : styles.aiRow]}>
        {!isUser && (
          <View style={styles.aiAvatar}>
            <Ionicons name="medical" size={16} color="#fff" />
          </View>
        )}
        
        <View style={styles.messageWrapper}>
          <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
            <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
              {item.content}
            </Text>
          </View>

          <Text style={[styles.timestamp, isUser ? styles.timestampUser : styles.timestampAi]}>
            {formatTime(item.created_date)}
          </Text>

          {!isUser && item.suggestions && item.suggestions.length > 0 && (
            <View style={styles.suggestionContainer}>
              {item.suggestions.map((sug, index) => (
                <TouchableOpacity 
                  key={index} 
                  style={styles.suggestionChip}
                  onPress={() => handleSend(sug)}
                >
                  <Text style={styles.suggestionText}>{sug}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton} activeOpacity={0.7}>
            <Ionicons name="arrow-back" size={24} color="#333" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Trợ lý AI Bạch Mai</Text>
          <View style={{ width: 24 }} />
        </View>

        <View style={styles.warningBanner}>
          <Ionicons name="warning" size={16} color="#d97706" style={{ marginRight: 6 }} />
          <Text style={styles.warningText}>
            Thông tin từ AI chỉ mang tính tham khảo, không thay thế chẩn đoán bác sĩ.
          </Text>
        </View>

        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderMessage}
          contentContainerStyle={styles.listContent}
          keyboardShouldPersistTaps="handled"
        />

        {isLoading && (
          <View style={[styles.messageRow, styles.aiRow]}>
            <View style={styles.aiAvatar}>
              <Ionicons name="medical" size={16} color="#fff" />
            </View>
            <View style={[styles.bubble, styles.aiBubble, styles.loadingBubble]}>
              <View style={styles.dotsContainer}>
                <View style={[styles.dot, styles.dot1]} />
                <View style={[styles.dot, styles.dot2]} />
                <View style={[styles.dot, styles.dot3]} />
              </View>
            </View>
          </View>
        )}

        {/* Khung nhập liệu: Đã được căn chỉnh padding để ôm sát thanh Tab */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Nhập câu hỏi của bạn..."
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={500}
          />
          <TouchableOpacity 
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
            onPress={() => handleSend()}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="send" size={20} color="#fff" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f8f9fa' },
  container: { flex: 1 },
  header: {
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between',
    paddingHorizontal: 16, 
    paddingVertical: 12, 
    paddingTop: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1, 
    borderBottomColor: '#eee',
  },
  backButton: { padding: 8 },
  headerTitle: { fontSize: 18, fontWeight: '600', color: '#333' },
  warningBanner: {
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: '#fffbeb',
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderBottomWidth: 1, 
    borderBottomColor: '#fde68a',
  },
  warningText: { flex: 1, fontSize: 12, color: '#92400e', fontWeight: '500' },
  listContent: { padding: 16, paddingBottom: 8 },
  messageRow: { flexDirection: 'row', marginBottom: 16, alignItems: 'flex-end' },
  userRow: { justifyContent: 'flex-end' },
  aiRow: { justifyContent: 'flex-start' },
  aiAvatar: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: '#2f6fed',
    justifyContent: 'center', alignItems: 'center', marginRight: 8, marginBottom: 4,
  },
  messageWrapper: { maxWidth: '80%' },
  bubble: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 16 },
  userBubble: { backgroundColor: '#2f6fed', borderBottomRightRadius: 4 },
  aiBubble: { backgroundColor: '#fff', borderBottomLeftRadius: 4, borderWidth: 1, borderColor: '#e5e7eb' },
  loadingBubble: { paddingVertical: 14, paddingHorizontal: 18 },
  messageText: { fontSize: 15, lineHeight: 22 },
  userText: { color: '#fff' },
  aiText: { color: '#333' },
  timestamp: { fontSize: 10, color: '#9ca3af', marginTop: 4, marginHorizontal: 8 },
  timestampUser: { textAlign: 'right' },
  timestampAi: { textAlign: 'left' },
  suggestionContainer: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 },
  suggestionChip: {
    backgroundColor: '#e0e7ff', paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 16, marginRight: 8, marginBottom: 8, borderWidth: 1, borderColor: '#c7d2fe',
  },
  suggestionText: { color: '#3730a3', fontSize: 13, fontWeight: '500' },
  inputContainer: {
    flexDirection: 'row', 
    alignItems: 'flex-end', 
    padding: 12, 
    paddingBottom: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1, 
    borderTopColor: '#eee',
  },
  input: {
    flex: 1, backgroundColor: '#f3f4f6', borderRadius: 20, paddingHorizontal: 16,
    paddingVertical: 10, fontSize: 15, maxHeight: 100, marginRight: 8,
  },
  sendButton: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: '#2f6fed',
    justifyContent: 'center', alignItems: 'center', marginBottom: 2,
  },
  sendButtonDisabled: { backgroundColor: '#93c5fd' },
  dotsContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#9ca3af' },
  dot1: { opacity: 0.4 },
  dot2: { opacity: 0.7 },
  dot3: { opacity: 1.0 },
});