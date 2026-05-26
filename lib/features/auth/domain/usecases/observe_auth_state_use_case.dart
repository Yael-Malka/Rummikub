import '../entities/auth_user.dart';
import '../repositories/phone_auth_repository.dart';

final class ObserveAuthStateUseCase {
  const ObserveAuthStateUseCase(this._repository);

  final PhoneAuthRepository _repository;

  Stream<AuthUser?> call() => _repository.authStateChanges();
}
