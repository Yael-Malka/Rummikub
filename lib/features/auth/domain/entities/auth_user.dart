/// Signed-in user snapshot (domain, no Firebase types).
final class AuthUser {
  const AuthUser({required this.phoneNumber});

  final String phoneNumber;
}
