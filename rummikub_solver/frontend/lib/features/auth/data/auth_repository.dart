// HTTP calls for login/register/verification.

import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../domain/auth_state.dart';

part 'auth_repository.g.dart';

class AuthRepository {
  final Dio _dio;

  AuthRepository(this._dio);

  Future<void> register(String email, String fullName, String password) async {
    await _dio.post(AppConstants.registerPath, data: {
      'email': email,
      'full_name': fullName,
      'password': password,
    });
  }

  Future<TokenResponse> login(String email, String password) async {
    final response = await _dio.post(AppConstants.loginPath, data: {
      'email': email,
      'password': password,
    });
    return TokenResponse.fromJson(response.data);
  }

  Future<void> verifyEmail(String token) async {
    await _dio.post(AppConstants.verifyEmailPath, data: {
      'token': token,
    });
  }

  Future<void> resendVerificationEmail(String email) async {
    await _dio.post('auth/resend-verification', data: {
      'email': email,
    });
  }

  Future<void> logout() async {
    try {
      await _dio.get(AppConstants.logoutPath);
    } catch (_) {
      // Ignore errors on logout
    }
  }
}

@riverpod
AuthRepository authRepository(Ref ref) {
  return AuthRepository(ref.watch(apiClientProvider));
}
