import '../../../game_engine/domain/entities/move.dart';

/// UI state for optimal-move search on a loaded simulation.
sealed class OptimalMovesState {
  const OptimalMovesState();
}

final class OptimalMovesIdle extends OptimalMovesState {
  const OptimalMovesIdle();
}

final class OptimalMovesLoading extends OptimalMovesState {
  const OptimalMovesLoading();
}

final class OptimalMovesLoaded extends OptimalMovesState {
  const OptimalMovesLoaded({
    required this.moves,
    required this.searchTimedOut,
  });

  final List<Move> moves;
  final bool searchTimedOut;
}

final class OptimalMovesError extends OptimalMovesState {
  const OptimalMovesError(this.message);

  final String message;
}
