import '../../domain/entities/game_state.dart';

/// Persisted simulation session on device.
final class SavedSession {
  const SavedSession({
    required this.gameState,
    required this.isFirstMeldTurn,
  });

  final GameState gameState;
  final bool isFirstMeldTurn;
}
