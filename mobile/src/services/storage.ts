import * as SecureStore from 'expo-secure-store';
import { REFRESH_TOKEN_KEY, TOKEN_KEY } from '../constants/config';

export const storage = {
  async saveToken(token: string) {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  },
  async getToken() {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  },
  async saveRefreshToken(refreshToken: string) {
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
  },
  async getRefreshToken() {
    return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  },
  async clearAll() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
  },
};