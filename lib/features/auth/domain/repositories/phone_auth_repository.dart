import '../entities/auth_user.dart';
import '../entities/phone_verification_session.dart';

/// Phone sign-in via Firebase (implemented in data layer).
abstract interface class PhoneAuthRepository {
  Stream<AuthUser?> authStateChanges();

  Future<PhoneVerificationSession> sendVerificationCode(String phoneE164);

  Future<AuthUser> verifyOtp({
    required String verificationId,
    required String smsCode,
  });

  Future<void> signOut();
}
