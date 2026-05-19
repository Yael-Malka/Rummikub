/// Outcome of a rules check (pure Dart).
sealed class ValidationResult {
  const ValidationResult();

  bool get isValid => this is ValidationSuccess;
  String? get message => switch (this) {
        ValidationSuccess() => null,
        ValidationFailure(:final reason) => reason,
      };
}

final class ValidationSuccess extends ValidationResult {
  const ValidationSuccess();
}

final class ValidationFailure extends ValidationResult {
  const ValidationFailure(this.reason);

  final String reason;
}
