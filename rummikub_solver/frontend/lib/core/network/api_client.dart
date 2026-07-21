// Shared Dio client with auth interceptor.

import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../storage/secure_storage.dart';
import 'auth_interceptor.dart';

part 'api_client.g.dart';

/// Reads JWT from secure storage.
@Riverpod(keepAlive: true)
SecureStorage secureStorage(Ref ref) {
  return SecureStorage();
}

/// Shared Dio instance for all API calls.
///
/// Base URL is /api/v1/ on web (nginx proxy) or 10.0.2.2:8000 on Android emulator.
/// Attaches JWT from secure storage and maps server errors to readable messages.
@Riverpod(keepAlive: true)
Dio apiClient(Ref ref) {
  // Use relative path for web to utilize Nginx proxy, otherwise use default Android emulator localhost
  const String envBaseUrl = String.fromEnvironment('API_BASE_URL');
  final String baseUrl = envBaseUrl.isNotEmpty 
      ? (envBaseUrl.endsWith('/') ? envBaseUrl : '$envBaseUrl/') 
      : (kIsWeb ? '/api/v1/' : 'http://10.0.2.2:8000/api/v1/');

  final dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      contentType: 'application/json',
    ),
  );

  dio.interceptors.add(
    AuthInterceptor(
      getToken: () => ref.read(secureStorageProvider).getToken(),
      onUnauthorized: () async {
        await ref.read(secureStorageProvider).deleteToken();
      },
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onError: (DioException err, ErrorInterceptorHandler handler) {
        String friendlyMessage = 'An unexpected error occurred.';
        if (err.type == DioExceptionType.connectionTimeout || 
            err.type == DioExceptionType.receiveTimeout || 
            err.type == DioExceptionType.sendTimeout) {
          friendlyMessage = "Can't reach the server. Check your connection.";
        } else if (err.type == DioExceptionType.connectionError) {
          friendlyMessage = "No internet connection.";
        } else if (err.response != null) {
          final data = err.response?.data;
          if (data is Map<String, dynamic> && data['detail'] != null) {
             friendlyMessage = data['detail'].toString();
          } else {
             friendlyMessage = 'Server error (${err.response?.statusCode})';
          }
        }
        
        // Throw a custom error or just wrap the message
        final newErr = err.copyWith(message: friendlyMessage);
        handler.next(newErr);
      },
    ),
  );

  dio.interceptors.add(LogInterceptor(responseBody: true, requestBody: true));

  return dio;
}
