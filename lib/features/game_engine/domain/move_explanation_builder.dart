import '../../simulation/domain/entities/game_state.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_id.dart';
import 'entities/move.dart';
import 'entities/move_explanation.dart';
import 'joker_role_inferrer.dart';
import 'rules_validator.dart';

/// Builds [MoveExplanation] from before/after states (presentation-only logic).
abstract final class MoveExplanationBuilder {
  static MoveExplanation build({
    required GameState stateBefore,
    required Move move,
  }) {
    final playedRackIds = _playedRackTileIds(stateBefore.rack, move.finalRack);
    final tableIdsBefore = _tableTileIds(stateBefore.tableMelds);

    final diff = _diffMelds(
      beforeMelds: stateBefore.tableMelds,
      afterMelds: move.finalTableMelds,
      tableIdsBefore: tableIdsBefore,
      playedRackIds: playedRackIds,
    );

    final finalState = move.toGameState();
    final isValid = RulesValidator.validateGameState(finalState).isValid;

    return MoveExplanation(
      summary: MoveExplanationSummary(
        tilesPlayedFromRack: move.tilesPlayedFromRack,
        isTableValid: isValid,
        rackTilesRemaining: move.finalRack.length,
      ),
      before: _phaseFromMelds(stateBefore.tableMelds),
      after: _phaseFromMelds(move.finalTableMelds),
      highlightedRackTileIds: playedRackIds,
      steps: diff,
    );
  }

  static MoveTablePhase _phaseFromMelds(List<Meld> melds) {
    return MoveTablePhase(
      melds: [
        for (final meld in melds)
          ExplainedMeld(
            meld: meld,
            jokerRoles: JokerRoleInferrer.forMeld(meld),
          ),
      ],
    );
  }

  static Set<TileId> _tableTileIds(List<Meld> melds) {
    return melds.expand((m) => m.tiles).map((t) => t.id).toSet();
  }

  static Set<TileId> _playedRackTileIds(
    List<Tile> rackBefore,
    List<Tile> rackAfter,
  ) {
    final remaining = rackAfter.map((t) => t.id).toSet();
    return rackBefore
        .where((t) => !remaining.contains(t.id))
        .map((t) => t.id)
        .toSet();
  }

  static List<Tile> _tableTilesInMeld(Meld meld, Set<TileId> tableIdsBefore) {
    return meld.tiles.where((t) => tableIdsBefore.contains(t.id)).toList();
  }

  static List<MoveExplanationStep> _diffMelds({
    required List<Meld> beforeMelds,
    required List<Meld> afterMelds,
    required Set<TileId> tableIdsBefore,
    required Set<TileId> playedRackIds,
  }) {
    final extends_ = <_ExtendMatch>[];
    final usedAfter = <int>{};

    for (var bi = 0; bi < beforeMelds.length; bi++) {
      final before = beforeMelds[bi];
      _ExtendMatch? best;

      for (var ai = 0; ai < afterMelds.length; ai++) {
        if (usedAfter.contains(ai)) {
          continue;
        }
        final after = afterMelds[ai];
        final added = _extendAddedTiles(
          before: before,
          after: after,
          tableIdsBefore: tableIdsBefore,
          playedRackIds: playedRackIds,
        );
        if (added == null) {
          continue;
        }

        final tableCount = _tableTilesInMeld(before, tableIdsBefore).length;
        if (best == null || tableCount > best.tableTileCount) {
          best = _ExtendMatch(
            beforeIndex: bi,
            afterIndex: ai,
            before: before,
            after: after,
            addedTiles: added,
            tableTileCount: tableCount,
          );
        }
      }

      if (best != null) {
        extends_.add(best);
        usedAfter.add(best.afterIndex);
      }
    }

    final usedBefore = extends_.map((e) => e.beforeIndex).toSet();
    final breaks = <BreakMeldStep>[];
    final builds = <BuildMeldStep>[];
    final extendSteps = <ExtendMeldStep>[];

    for (var bi = 0; bi < beforeMelds.length; bi++) {
      if (!usedBefore.contains(bi)) {
        breaks.add(BreakMeldStep(beforeMeld: beforeMelds[bi]));
      }
    }

    for (var ai = 0; ai < afterMelds.length; ai++) {
      if (!usedAfter.contains(ai)) {
        builds.add(BuildMeldStep(afterMeld: afterMelds[ai]));
      }
    }

    for (final match in extends_) {
      extendSteps.add(
        ExtendMeldStep(
          beforeMeld: match.before,
          afterMeld: match.after,
          addedTiles: match.addedTiles,
        ),
      );
    }

    return [...breaks, ...builds, ...extendSteps];
  }

  static List<Tile>? _extendAddedTiles({
    required Meld before,
    required Meld after,
    required Set<TileId> tableIdsBefore,
    required Set<TileId> playedRackIds,
  }) {
    if (before.type != after.type) {
      return null;
    }

    final tableBefore = _tableTilesInMeld(before, tableIdsBefore);
    if (tableBefore.isEmpty) {
      return null;
    }

    final tableBeforeIds = tableBefore.map((t) => t.id).toSet();
    if (!tableBeforeIds.every(
      (id) => after.tiles.any((t) => t.id == id),
    )) {
      return null;
    }

    final added = after.tiles.where((t) => !tableBeforeIds.contains(t.id)).toList();
    if (added.isEmpty) {
      return null;
    }

    if (!added.every((t) => playedRackIds.contains(t.id))) {
      return null;
    }

    return added;
  }
}

final class _ExtendMatch {
  const _ExtendMatch({
    required this.beforeIndex,
    required this.afterIndex,
    required this.before,
    required this.after,
    required this.addedTiles,
    required this.tableTileCount,
  });

  final int beforeIndex;
  final int afterIndex;
  final Meld before;
  final Meld after;
  final List<Tile> addedTiles;
  final int tableTileCount;
}
