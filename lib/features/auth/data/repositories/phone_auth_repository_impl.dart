import '../../domain/entities/auth_user.dart';
import '../../domain/entities/phone_verification_session.dart';
import '../../domain/exceptions/auth_exceptions.dart';
import '../../domain/repositories/phone_auth_repository.dart';
import '../datasources/firebase_phone_auth_data_source.dart';

final class PhoneAuthRepositoryImpl implements PhoneAuthRepository {
  PhoneAuthRepositoryImpl(this._dataSource);

  final FirebasePhoneAuthDataSource _dataSource;

  @override
  Stream<AuthUser?> authStateChanges() => _dataSource.authStateChanges();

  @override
  Future<PhoneVerificationSession> sendVerificationCode(String phoneE164) async {
    try {
      return await _dataSource.sendVerificationCode(phoneE164);
    } on PhoneVerificationFailedException {
      rethrow;
    } catch (_) {
      throw const PhoneVerificationFailedException();
    }
  }

  @override
  Future<AuthUser> verifyOtp({
    required String verificationId,
    required String smsCode,
  }) async {
    try {
      return await _dataSource.verifyOtp(
        verificationId: verificationId,
        smsCode: smsCode,
      );
    } on OtpVerificationFailedException {
      rethrow;
    } catch (_) {
      throw const OtpVerificationFailedException();
    }
  }

  @override
  Future<void> signOut() => _dataSource.signOut();
}
