// Persist the auth token locally with SharedPreferences.

import 'package:shared_preferences/shared_preferences.dart';

class SecureStorage {
  SecureStorage();

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_access_token', token);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_access_token');
  }

  Future<void> deleteToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_access_token');
  }

  Future<bool> hasToken() async {
    final token = await getToken();
    return token != null;
  }
}
