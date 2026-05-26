import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/auth/domain/entities/auth_user.dart';
import 'package:rummikub_app/features/auth/domain/entities/phone_verification_session.dart';
import 'package:rummikub_app/features/auth/domain/exceptions/auth_exceptions.dart';
import 'package:rummikub_app/features/auth/domain/repositories/phone_auth_repository.dart';
import 'package:rummikub_app/features/auth/domain/usecases/send_phone_verification_use_case.dart';
import 'package:rummikub_app/features/auth/domain/usecases/verify_phone_otp_use_case.dart';
import 'package:rummikub_app/features/auth/presentation/providers/auth_view_model.dart';

final class _FakePhoneAuthRepository implements PhoneAuthRepository {
  bool failSend = false;
  bool failVerify = false;
  String? lastPhoneE164;
  String? lastSmsCode;

  @override
  Stream<AuthUser?> authStateChanges() => const Stream.empty();

  @override
  Future<PhoneVerificationSession> sendVerificationCode(String phoneE164) async {
    lastPhoneE164 = phoneE164;
    if (failSend) {
      throw const PhoneVerificationFailedException();
    }
    return const PhoneVerificationSession(verificationId: 'test-id');
  }

  @override
  Future<AuthUser> verifyOtp({
    required String verificationId,
    required String smsCode,
  }) async {
    lastSmsCode = smsCode;
    if (failVerify) {
      throw const OtpVerificationFailedException();
    }
    return const AuthUser(phoneNumber: '+972501234567');
  }

  @override
  Future<void> signOut() async {}
}

void main() {
  late _FakePhoneAuthRepository repository;
  late AuthViewModel viewModel;

  setUp(() {
    repository = _FakePhoneAuthRepository();
    viewModel = AuthViewModel(
      sendVerification: SendPhoneVerificationUseCase(repository),
      verifyOtp: VerifyPhoneOtpUseCase(repository),
    );
  });

  test('givenValidPhone_whenSendCode_thenVerificationIdSet', () async {
    viewModel.setPhoneInput('0501234567');

    await viewModel.sendVerificationCode();

    expect(viewModel.verificationId, 'test-id');
    expect(repository.lastPhoneE164, '+972501234567');
    expect(viewModel.phoneError, isNull);
  });

  test('givenInvalidPhone_whenSendCode_thenPhoneError', () async {
    viewModel.setPhoneInput('123');

    await viewModel.sendVerificationCode();

    expect(viewModel.verificationId, isNull);
    expect(viewModel.phoneError, isNotNull);
  });

  test('givenShortOtp_whenVerify_thenOtpError', () async {
    viewModel.setPhoneInput('0501234567');
    await viewModel.sendVerificationCode();
    viewModel.setOtpCode('12');

    final success = await viewModel.verifyOtpCode();

    expect(success, isFalse);
    expect(viewModel.otpError, isNotNull);
  });

  test('givenValidOtp_whenVerify_thenSuccess', () async {
    viewModel.setPhoneInput('0501234567');
    await viewModel.sendVerificationCode();
    viewModel.setOtpCode('123456');

    final success = await viewModel.verifyOtpCode();

    expect(success, isTrue);
    expect(repository.lastSmsCode, '123456');
  });

  test('whenReset_thenClearsState', () async {
    viewModel.setPhoneInput('0501234567');
    await viewModel.sendVerificationCode();

    viewModel.resetPhoneAuthState();

    expect(viewModel.verificationId, isNull);
    expect(viewModel.phoneInput, isEmpty);
  });
}
