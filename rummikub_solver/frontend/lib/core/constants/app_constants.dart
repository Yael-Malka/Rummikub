// API base URL and endpoint paths.

class AppConstants {
  static const String defaultApiBaseUrl = 'http://10.0.2.2:8000/api';

  static const String accessTokenKey = 'auth_access_token';

  // API Paths
  static const String registerPath = 'auth/register';
  static const String loginPath = 'auth/login';
  static const String verifyEmailPath = 'auth/verify';
  static const String logoutPath = 'auth/logout';
}
