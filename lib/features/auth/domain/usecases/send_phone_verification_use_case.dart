import '../entities/phone_verification_session.dart';
import '../exceptions/auth_exceptions.dart';
import '../repositories/phone_auth_repository.dart';
import '../utils/israel_phone_normalizer.dart';

final class SendPhoneVerificationUseCase {
  const SendPhoneVerificationUseCase(this._repository);

  final PhoneAuthRepository _repository;

  Future<PhoneVerificationSession> call(String localPhoneInput) {
    final validationError = IsraelPhoneNormalizer.validateLocalNumber(
      localPhoneInput,
    );
    if (validationError != null) {
      throw const InvalidPhoneException();
    }

    final phoneE164 = IsraelPhoneNormalizer.toE164(localPhoneInput);
    return _repository.sendVerificationCode(phoneE164);
  }
}
