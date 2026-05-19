/// Thrown when a valid simulated state could not be produced.
final class StateGenerationException implements Exception {
  const StateGenerationException([this.message = 'Failed to generate game state']);

  final String message;

  @override
  String toString() => 'StateGenerationException: $message';
}
