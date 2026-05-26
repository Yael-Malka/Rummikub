import '../entities/auth_user.dart';
import '../repositories/phone_auth_repository.dart';

final class VerifyPhoneOtpUseCase {
  const VerifyPhoneOtpUseCase(this._repository);

  final PhoneAuthRepository _repository;

  Future<AuthUser> call({
    required String verificationId,
    required String smsCode,
  }) {
    return _repository.verifyOtp(
      verificationId: verificationId,
      smsCode: smsCode,
    );
  }
}
