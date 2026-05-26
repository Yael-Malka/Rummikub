import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';

import '../../features/auth/data/datasources/firebase_phone_auth_data_source.dart';
import '../../features/auth/data/repositories/phone_auth_repository_impl.dart';
import '../../features/auth/domain/repositories/phone_auth_repository.dart';
import '../../features/auth/domain/usecases/observe_auth_state_use_case.dart';
import '../../features/auth/domain/usecases/send_phone_verification_use_case.dart';
import '../../features/auth/domain/usecases/sign_out_use_case.dart';
import '../../features/auth/domain/usecases/verify_phone_otp_use_case.dart';
import '../../features/auth/presentation/providers/auth_view_model.dart';

/// Authentication dependency injection.
abstract final class AuthProviders {
  static List<SingleChildWidget> get providers => [
        Provider<FirebasePhoneAuthDataSource>(
          create: (_) => FirebasePhoneAuthDataSource(),
        ),
        Provider<PhoneAuthRepository>(
          create: (context) => PhoneAuthRepositoryImpl(
            context.read<FirebasePhoneAuthDataSource>(),
          ),
        ),
        Provider<SendPhoneVerificationUseCase>(
          create: (context) => SendPhoneVerificationUseCase(
            context.read<PhoneAuthRepository>(),
          ),
        ),
        Provider<VerifyPhoneOtpUseCase>(
          create: (context) => VerifyPhoneOtpUseCase(
            context.read<PhoneAuthRepository>(),
          ),
        ),
        Provider<ObserveAuthStateUseCase>(
          create: (context) => ObserveAuthStateUseCase(
            context.read<PhoneAuthRepository>(),
          ),
        ),
        Provider<SignOutUseCase>(
          create: (context) => SignOutUseCase(
            context.read<PhoneAuthRepository>(),
          ),
        ),
        ChangeNotifierProvider<AuthViewModel>(
          create: (context) => AuthViewModel(
            sendVerification: context.read<SendPhoneVerificationUseCase>(),
            verifyOtp: context.read<VerifyPhoneOtpUseCase>(),
          ),
        ),
      ];
}
