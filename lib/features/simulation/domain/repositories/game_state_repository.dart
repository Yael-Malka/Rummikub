import '../entities/game_state.dart';

/// Provides simulated Rummikub game states.
abstract interface class GameStateRepository {
  GameState generateSimulatedState();
}
