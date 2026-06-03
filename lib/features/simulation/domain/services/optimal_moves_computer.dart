import 'package:flutter/foundation.dart';

import '../../../../core/services/solver_logger.dart';
import '../../../game_engine/domain/entities/optimal_moves_result.dart';
import '../../../game_engine/domain/usecases/find_optimal_moves_use_case.dart';
import '../../data/models/game_state_codec.dart';
import '../entities/game_state.dart';

/// Payload sent to the background isolate for move search.
final class OptimalMovesIsolateInput {
  const OptimalMovesIsolateInput({
    required this.encodedState,
    required this.isFirstMeldTurn,
  });

  final Map<String, dynamic> encodedState;
  final bool isFirstMeldTurn;
}

OptimalMovesResult _findOptimalMovesIsolate(OptimalMovesIsolateInput input) {
  SolverLogger.info('Isolate compute started');
  final stopwatch = Stopwatch()..start();
  final state = GameStateCodec.decodeState(input.encodedState);
  if (state == null) {
    SolverLogger.warn('Isolate: failed to decode game state');
    return OptimalMovesResult.empty;
  }
  final result = const FindOptimalMovesUseCase()(
    state,
    isFirstMeldTurn: input.isFirstMeldTurn,
  );
  SolverLogger.info(
    'Isolate compute finished in ${stopwatch.elapsed.inMilliseconds}ms '
    '(${result.moves.length} moves, timedOut=${result.searchTimedOut})',
  );
  return result;
}

/// Runs move search on a worker isolate so the UI can show a spinner.
abstract final class OptimalMovesComputer {
  /// When false, runs on the main isolate (for widget tests only).
  static bool useBackgroundIsolate = true;

  static Future<OptimalMovesResult> run(
    GameState state, {
    required bool isFirstMeldTurn,
  }) {
    final input = OptimalMovesIsolateInput(
      encodedState: GameStateCodec.encodeState(state),
      isFirstMeldTurn: isFirstMeldTurn,
    );

    SolverLogger.info(
      'Scheduling search (background=$useBackgroundIsolate)',
    );

    if (!useBackgroundIsolate) {
      return Future<OptimalMovesResult>.value(_findOptimalMovesIsolate(input));
    }

    return compute(_findOptimalMovesIsolate, input).then((result) {
      SolverLogger.info(
        'Main isolate received ${result.moves.length} moves '
        '(timedOut=${result.searchTimedOut})',
      );
      return result;
    });
  }
}
