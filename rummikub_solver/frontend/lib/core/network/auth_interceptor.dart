// Attach JWT to outgoing requests.

import 'package:dio/dio.dart';

class AuthInterceptor extends QueuedInterceptor {
  final Future<String?> Function() getToken;
  final Future<void> Function() onUnauthorized;

  AuthInterceptor({
    required this.getToken,
    required this.onUnauthorized,
  });

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      final currentToken = await getToken();
      final requestToken = err.requestOptions.headers['Authorization']
          ?.toString()
          .replaceFirst('Bearer ', '');
          
      // Only log out if the token that caused the 401 is still the current active token.
      if (currentToken == null || requestToken == currentToken) {
        await onUnauthorized();
      }
    }
    handler.next(err);
  }
}
