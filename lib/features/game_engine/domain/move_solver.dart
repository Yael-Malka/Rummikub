import '../../../core/constants/solver_constants.dart';
import '../../simulation/domain/entities/game_state.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/tile.dart';
import 'entities/move.dart';
import 'meld_partitioner.dart';
import 'rules_validator.dart';

/// Finds legal moves that maximize tiles played from the rack.
abstract final class MoveSolver {
  static List<Move> findOptimalMoves(
    GameState state, {
    required bool isFirstMeldTurn,
    Duration timeout = SolverConstants.searchTimeout,
  }) {
    final stopwatch = Stopwatch()..start();
    final initialRack = List<Tile>.from(state.rack);
    final tableTiles = [
      for (final meld in state.tableMelds) ...meld.tiles,
    ];

    var bestCount = -1;
    final bestMoves = <Move>[];

    void consider(List<Tile> playedFromRack, List<Meld> finalMelds) {
      final remainingRack = initialRack
          .where((t) => !playedFromRack.any((p) => p.id == t.id))
          .toList();

      final resultState = GameState(
        rack: remainingRack,
        tableMelds: finalMelds,
      );

      if (!RulesValidator.validateGameState(resultState).isValid) {
        return;
      }

      final playedCount = playedFromRack.length;
      if (isFirstMeldTurn && playedCount > 0) {
        final score = RulesValidator.scoreTilesFromRack(playedFromRack);
        if (!RulesValidator.meetsInitialMeldRequirement(score)) {
          return;
        }
      }

      final move = Move(
        tilesPlayedFromRack: playedCount,
        finalTableMelds: finalMelds,
        finalRack: remainingRack,
      );

      if (playedCount > bestCount) {
        bestCount = playedCount;
        bestMoves
          ..clear()
          ..add(move);
      } else if (playedCount == bestCount && !bestMoves.contains(move)) {
        bestMoves.add(move);
      }
    }

    void searchRack(int index, List<Tile> played) {
      if (stopwatch.elapsed >= timeout) {
        return;
      }

      if (index == initialRack.length) {
        final pool = [...tableTiles, ...played];
        final partitions = MeldPartitioner.findAllPartitions(
          pool,
          maxResults: SolverConstants.maxPartitionsPerPool,
        );

        if (partitions.isEmpty) {
          if (played.isEmpty && state.tableMelds.isNotEmpty) {
            consider(const [], state.tableMelds);
          }
          return;
        }

        for (final melds in partitions) {
          consider(played, melds);
        }
        return;
      }

      searchRack(index + 1, [...played, initialRack[index]]);
      searchRack(index + 1, played);
    }

    searchRack(0, []);

    if (bestMoves.isEmpty &&
        RulesValidator.validateGameState(state).isValid &&
        initialRack.isEmpty) {
      return [
        Move(
          tilesPlayedFromRack: 0,
          finalTableMelds: state.tableMelds,
          finalRack: const [],
        ),
      ];
    }

    return bestMoves;
  }
}
