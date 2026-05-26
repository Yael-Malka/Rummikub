import '../repositories/phone_auth_repository.dart';

final class SignOutUseCase {
  const SignOutUseCase(this._repository);

  final PhoneAuthRepository _repository;

  Future<void> call() => _repository.signOut();
}
