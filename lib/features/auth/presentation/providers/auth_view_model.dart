import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/constants/auth_constants.dart';
import '../../domain/exceptions/auth_exceptions.dart';
import '../../domain/usecases/send_phone_verification_use_case.dart';
import '../../domain/usecases/verify_phone_otp_use_case.dart';

final class AuthViewModel extends ChangeNotifier {
  AuthViewModel({
    required SendPhoneVerificationUseCase sendVerification,
    required VerifyPhoneOtpUseCase verifyOtp,
  })  : _sendVerification = sendVerification,
        _verifyOtp = verifyOtp;

  final SendPhoneVerificationUseCase _sendVerification;
  final VerifyPhoneOtpUseCase _verifyOtp;

  String _phoneInput = '';
  String? _phoneError;
  bool _isSendingCode = false;
  String? _verificationId;

  String _otpCode = '';
  bool _isVerifyingOtp = false;
  String? _otpError;

  int _resendCooldownSeconds = 0;
  Timer? _resendTimer;

  String get phoneInput => _phoneInput;
  String? get phoneError => _phoneError;
  bool get isSendingCode => _isSendingCode;
  String? get verificationId => _verificationId;
  String get otpCode => _otpCode;
  bool get isVerifyingOtp => _isVerifyingOtp;
  String? get otpError => _otpError;
  int get resendCooldownSeconds => _resendCooldownSeconds;
  bool get canResendCode => _resendCooldownSeconds == 0;

  void setPhoneInput(String value) {
    _phoneInput = value;
    _phoneError = null;
    notifyListeners();
  }

  void setOtpCode(String value) {
    _otpCode = value;
    _otpError = null;
    notifyListeners();
  }

  Future<void> sendVerificationCode() async {
    _isSendingCode = true;
    _phoneError = null;
    _verificationId = null;
    notifyListeners();

    try {
      final session = await _sendVerification(_phoneInput);
      _verificationId = session.verificationId;
      _startResendCooldown();
    } on InvalidPhoneException {
      _phoneError = AppStrings.invalidPhoneError;
    } on PhoneVerificationFailedException {
      _phoneError = AppStrings.genericAuthError;
    } catch (_) {
      _phoneError = AppStrings.genericAuthError;
    } finally {
      _isSendingCode = false;
      notifyListeners();
    }
  }

  Future<bool> verifyOtpCode() async {
    if (_otpCode.length != AuthConstants.otpLength) {
      _otpError = AppStrings.invalidOtpError;
      notifyListeners();
      return false;
    }

    if (_verificationId == null) {
      _otpError = AppStrings.genericAuthError;
      notifyListeners();
      return false;
    }

    _isVerifyingOtp = true;
    _otpError = null;
    notifyListeners();

    try {
      await _verifyOtp(
        verificationId: _verificationId!,
        smsCode: _otpCode,
      );
      _isVerifyingOtp = false;
      notifyListeners();
      return true;
    } on OtpVerificationFailedException {
      _otpError = AppStrings.otpVerificationFailed;
    } catch (_) {
      _otpError = AppStrings.otpVerificationFailed;
    }

    _isVerifyingOtp = false;
    notifyListeners();
    return false;
  }

  Future<void> resendCode() async {
    if (!canResendCode) {
      return;
    }

    _verificationId = null;
    await sendVerificationCode();
  }

  void resetPhoneAuthState() {
    _phoneInput = '';
    _phoneError = null;
    _isSendingCode = false;
    _verificationId = null;
    _otpCode = '';
    _isVerifyingOtp = false;
    _otpError = null;
    _resendTimer?.cancel();
    _resendTimer = null;
    _resendCooldownSeconds = 0;
    notifyListeners();
  }

  void _startResendCooldown() {
    _resendCooldownSeconds = AuthConstants.resendCooldownSeconds;
    _resendTimer?.cancel();

    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCooldownSeconds > 0) {
        _resendCooldownSeconds--;
        notifyListeners();
      } else {
        timer.cancel();
        _resendTimer = null;
      }
    });
  }

  @override
  void dispose() {
    _resendTimer?.cancel();
    super.dispose();
  }
}
