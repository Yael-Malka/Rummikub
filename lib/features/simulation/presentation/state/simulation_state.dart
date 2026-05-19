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

final class SimulationError extends SimulationState {
  const SimulationError(this.message);

  final String message;
}
