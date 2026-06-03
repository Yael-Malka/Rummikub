import '../../../simulation/domain/entities/game_state.dart';
import '../entities/optimal_moves_result.dart';
import '../move_solver.dart';

/// All moves that play the most rack tiles this turn (ties included).
final class FindOptimalMovesUseCase {
  const FindOptimalMovesUseCase();

  OptimalMovesResult call(
    GameState state, {
    required bool isFirstMeldTurn,
  }) {
    return MoveSolver.findOptimalMoves(
      state,
      isFirstMeldTurn: isFirstMeldTurn,
    );
  }
}
