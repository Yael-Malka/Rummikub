import '../../simulation/domain/entities/game_state.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/tile.dart';
import 'entities/move.dart';
import 'entities/move_step.dart';

/// Builds human-facing move steps from before/after game states.
abstract final class MoveStepsBuilder {
  static List<MoveStep> buildSteps({
    required GameState stateBefore,
    required Move move,
  }) {
    final played = _tilesPlayedFromRack(stateBefore.rack, move.finalRack);
    final steps = <MoveStep>[];

    if (played.isNotEmpty) {
      steps.add(PlayTilesFromRackStep(played));
    }

    if (_tableLayoutChanged(stateBefore.tableMelds, move.finalTableMelds)) {
      steps.add(
        ReorganizeTableStep(
          meldsBeforeCount: stateBefore.tableMelds.length,
          meldsAfterCount: move.finalTableMelds.length,
        ),
      );
    }

    return steps;
  }

  static List<Tile> _tilesPlayedFromRack(
    List<Tile> rackBefore,
    List<Tile> rackAfter,
  ) {
    final remainingIds = rackAfter.map((tile) => tile.id).toSet();
    return rackBefore.where((tile) => !remainingIds.contains(tile.id)).toList();
  }

  static bool _tableLayoutChanged(List<Meld> before, List<Meld> after) {
    final beforeKeys = before.map(Move.visualMeldKey).toList()..sort();
    final afterKeys = after.map(Move.visualMeldKey).toList()..sort();
    if (beforeKeys.length != afterKeys.length) {
      return true;
    }
    for (var index = 0; index < beforeKeys.length; index++) {
      if (beforeKeys[index] != afterKeys[index]) {
        return true;
      }
    }
    return false;
  }
}
