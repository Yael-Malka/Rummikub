/// Phone authentication configuration (Israel +972).
abstract final class AuthConstants {
  static const String phonePrefix = '+972';
  static const int otpLength = 6;
  static const int resendCooldownSeconds = 60;
  static const int minPhoneDigits = 9;
  static const int maxPhoneDigits = 10;

  AuthConstants._();
}
