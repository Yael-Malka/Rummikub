import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';

import '../../domain/entities/auth_user.dart';
import '../../domain/entities/phone_verification_session.dart';
import '../../domain/exceptions/auth_exceptions.dart';

/// Firebase Phone Auth SDK calls (data layer only).
final class FirebasePhoneAuthDataSource {
  FirebasePhoneAuthDataSource({FirebaseAuth? auth})
      : _auth = auth ?? FirebaseAuth.instance;

  final FirebaseAuth _auth;

  Stream<AuthUser?> authStateChanges() {
    return _auth.authStateChanges().map((user) {
      final phone = user?.phoneNumber;
      if (phone == null || phone.isEmpty) {
        return null;
      }
      return AuthUser(phoneNumber: phone);
    });
  }

  Future<PhoneVerificationSession> sendVerificationCode(String phoneE164) async {
    final completer = Completer<PhoneVerificationSession>();
    await _auth.verifyPhoneNumber(
      phoneNumber: phoneE164,
      verificationCompleted: (_) {},
      verificationFailed: (FirebaseAuthException e) {
        if (!completer.isCompleted) {
          completer.completeError(const PhoneVerificationFailedException());
        }
      },
      codeSent: (verificationId, _) {
        if (!completer.isCompleted) {
          completer.complete(
            PhoneVerificationSession(verificationId: verificationId),
          );
        }
      },
      codeAutoRetrievalTimeout: (verificationId) {
        if (!completer.isCompleted) {
          completer.complete(
            PhoneVerificationSession(verificationId: verificationId),
          );
        }
      },
      timeout: const Duration(seconds: 60),
    );

    return completer.future.timeout(
      const Duration(seconds: 65),
      onTimeout: () => throw const PhoneVerificationFailedException(),
    );
  }

  Future<AuthUser> verifyOtp({
    required String verificationId,
    required String smsCode,
  }) async {
    final credential = PhoneAuthProvider.credential(
      verificationId: verificationId,
      smsCode: smsCode,
    );

    final userCredential = await _auth.signInWithCredential(credential);
    final phone = userCredential.user?.phoneNumber;
    if (phone == null || phone.isEmpty) {
      throw const OtpVerificationFailedException();
    }

    return AuthUser(phoneNumber: phone);
  }

  Future<void> signOut() => _auth.signOut();
}
