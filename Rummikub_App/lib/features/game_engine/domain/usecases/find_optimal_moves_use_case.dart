import '../../../simulation/domain/entities/game_state.dart';
import '../entities/move.dart';
import '../move_solver.dart';

/// All moves that play the most rack tiles this turn (ties included).
final class FindOptimalMovesUseCase {
  const FindOptimalMovesUseCase();

  List<Move> call(
    GameState state, {
    required bool isFirstMeldTurn,
  }) {
    return MoveSolver.findOptimalMoves(
      state,
      isFirstMeldTurn: isFirstMeldTurn,
    );
  }
}
