// Riverpod auth notifier.

import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:dio/dio.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/network/api_client.dart';
import '../../data/auth_repository.dart';
import '../../domain/auth_state.dart';

part 'auth_provider.g.dart';

@Riverpod(keepAlive: true)
class AuthNotifier extends _$AuthNotifier {
  AuthRepository get _repository => ref.read(authRepositoryProvider);
  SecureStorage get _storage => ref.read(secureStorageProvider);

  @override
  Future<AuthState> build() async {
    final hasToken = await _storage.hasToken();
    if (hasToken) {
      return const AuthState(status: AuthStatus.authenticated);
    }
    return const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> loginWithEmail(String email, String password) async {
    state = const AsyncValue.data(AuthState(status: AuthStatus.loading));
    try {
      final tokenResponse = await _repository.login(email, password);
      await _storage.saveToken(tokenResponse.accessToken);
      state = AsyncValue.data(AuthState(
        status: AuthStatus.authenticated,
        user: tokenResponse.user,
      ));
    } on DioException catch (e) {
      final detail = e.response?.data['detail'];
      final message = detail is String ? detail : (detail?.toString() ?? e.message ?? 'Login failed');
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: message,
      ));
    } catch (e) {
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }

  Future<void> register(String email, String fullName, String password) async {
    state = const AsyncValue.data(AuthState(status: AuthStatus.loading));
    try {
      await _repository.register(email, fullName, password);
      state = const AsyncValue.data(AuthState(status: AuthStatus.unauthenticated));
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : null;
      final message = detail is String
          ? detail
          : (detail?.toString() ?? e.message ?? 'Registration failed');
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: message,
      ));
    } catch (e) {
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }

  Future<void> verifyEmail(String token) async {
    state = const AsyncValue.data(AuthState(status: AuthStatus.loading));
    try {
      await _repository.verifyEmail(token);
      state = const AsyncValue.data(AuthState(status: AuthStatus.unauthenticated));
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : null;
      final message = detail is String
          ? detail
          : (detail?.toString() ?? e.message ?? 'Verification failed');
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: message,
      ));
    } catch (e) {
      state = AsyncValue.data(AuthState(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }

  Future<void> resendVerificationEmail(String email) async {
    try {
      await _repository.resendVerificationEmail(email);
    } catch (e) {
      rethrow;
    }
  }

  Future<void> logout() async {
    state = const AsyncValue.data(AuthState(status: AuthStatus.loading));
    await _repository.logout();
    await _storage.deleteToken();
    state = const AsyncValue.data(AuthState(status: AuthStatus.unauthenticated));
  }
}
