import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/auth/domain/utils/israel_phone_normalizer.dart';

void main() {
  group('IsraelPhoneNormalizer', () {
    test('givenLocalWithLeadingZero_whenToE164_thenPlus972', () {
      expect(
        IsraelPhoneNormalizer.toE164('0501234567'),
        '+972501234567',
      );
    });

    test('givenLocalWithoutLeadingZero_whenToE164_thenPlus972', () {
      expect(
        IsraelPhoneNormalizer.toE164('501234567'),
        '+972501234567',
      );
    });

    test('givenFormattedInput_whenToE164_thenStripsNonDigits', () {
      expect(
        IsraelPhoneNormalizer.toE164('050-123-4567'),
        '+972501234567',
      );
    });

    test('givenTooShort_whenValidate_thenInvalid', () {
      expect(
        IsraelPhoneNormalizer.validateLocalNumber('05012'),
        isNotNull,
      );
    });

    test('givenValidNineDigits_whenValidate_thenNull', () {
      expect(
        IsraelPhoneNormalizer.validateLocalNumber('501234567'),
        isNull,
      );
    });
  });
}
