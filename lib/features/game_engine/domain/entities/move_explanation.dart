import '../../../simulation/domain/entities/meld.dart';
import '../../../simulation/domain/entities/tile.dart';
import '../../../simulation/domain/entities/tile_color.dart';
import '../../../simulation/domain/entities/tile_id.dart';

/// Full human-facing explanation for one optimal move.
final class MoveExplanation {
  const MoveExplanation({
    required this.summary,
    required this.before,
    required this.after,
    required this.highlightedRackTileIds,
    required this.steps,
  });

  final MoveExplanationSummary summary;
  final MoveTablePhase before;
  final MoveTablePhase after;
  final Set<TileId> highlightedRackTileIds;
  final List<MoveExplanationStep> steps;

  bool isHighlighted(TileId id) => highlightedRackTileIds.contains(id);
}

/// Level 1 — short outcome line.
final class MoveExplanationSummary {
  const MoveExplanationSummary({
    required this.tilesPlayedFromRack,
    required this.isTableValid,
    required this.rackTilesRemaining,
  });

  final int tilesPlayedFromRack;
  final bool isTableValid;
  final int rackTilesRemaining;
}

/// Table melds at one point in the move (before or after).
final class MoveTablePhase {
  const MoveTablePhase({required this.melds});

  final List<ExplainedMeld> melds;
}

/// One meld with optional joker role hints for the UI.
final class ExplainedMeld {
  const ExplainedMeld({
    required this.meld,
    required this.jokerRoles,
  });

  final Meld meld;
  final List<JokerRole> jokerRoles;
}

/// What a joker represents inside a legal meld.
final class JokerRole {
  const JokerRole({
    required this.jokerTileId,
    required this.standsInForNumber,
    this.standsInForColor,
  });

  final TileId jokerTileId;
  final int standsInForNumber;
  final TileColor? standsInForColor;
}

/// Level 3 — minimal meaningful table actions.
sealed class MoveExplanationStep {
  const MoveExplanationStep();
}

/// A table meld from before no longer exists as one set.
final class BreakMeldStep extends MoveExplanationStep {
  const BreakMeldStep({required this.beforeMeld});

  final Meld beforeMeld;
}

/// A new meld appears on the table after the move.
final class BuildMeldStep extends MoveExplanationStep {
  const BuildMeldStep({required this.afterMeld});

  final Meld afterMeld;
}

/// Same table tiles stay together; rack tiles were added to the set.
final class ExtendMeldStep extends MoveExplanationStep {
  const ExtendMeldStep({
    required this.beforeMeld,
    required this.afterMeld,
    required this.addedTiles,
  });

  final Meld beforeMeld;
  final Meld afterMeld;
  final List<Tile> addedTiles;
}
