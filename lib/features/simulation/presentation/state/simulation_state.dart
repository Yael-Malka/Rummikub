import '../../domain/entities/game_state.dart';

/// UI state for the simulation screen (sealed hierarchy per project rules).
sealed class SimulationState {
  const SimulationState();
}

final class SimulationInitial extends SimulationState {
  const SimulationInitial();
}

final class SimulationLoading extends SimulationState {
  const SimulationLoading();
}

final class SimulationLoaded extends SimulationState {
  const SimulationLoaded(this.gameState);

  final GameState gameState;
}

final class SimulationError extends SimulationState {
  const SimulationError(this.message);

  final String message;
}
