import '../../../simulation/domain/entities/game_state.dart';
import '../entities/move.dart';
import '../move_solver.dart';

/// Returns all moves that play the maximum number of rack tiles.
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
