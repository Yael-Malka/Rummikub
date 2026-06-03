import '../../../core/constants/solver_constants.dart';
import '../../simulation/domain/entities/game_state.dart';
import 'entities/optimal_moves_result.dart';
import 'set_cover_move_solver.dart';

/// Entry point for optimal-move search (max rack tiles played).
abstract final class MoveSolver {
  static OptimalMovesResult findOptimalMoves(
    GameState state, {
    required bool isFirstMeldTurn,
    Duration timeout = SolverConstants.searchTimeout,
  }) {
    return SetCoverMoveSolver.findOptimalMoves(
      state,
      isFirstMeldTurn: isFirstMeldTurn,
      timeout: timeout,
    );
  }
}
