import '../../../../core/constants/auth_constants.dart';

/// Validates and normalizes Israeli local phone numbers to E.164 (+972).
abstract final class IsraelPhoneNormalizer {
  static String? validateLocalNumber(String input) {
    final digitsOnly = input.replaceAll(RegExp(r'[^0-9]'), '');

    if (digitsOnly.isEmpty) {
      return 'invalid';
    }

    if (digitsOnly.length < AuthConstants.minPhoneDigits ||
        digitsOnly.length > AuthConstants.maxPhoneDigits) {
      return 'invalid';
    }

    return null;
  }

  static String toE164(String input) {
    final digitsOnly = input.replaceAll(RegExp(r'[^0-9]'), '');
    final withoutLeadingZero =
        digitsOnly.startsWith('0') ? digitsOnly.substring(1) : digitsOnly;

    return '${AuthConstants.phonePrefix}$withoutLeadingZero';
  }
}
