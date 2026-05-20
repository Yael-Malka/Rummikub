import '../../../simulation/domain/entities/tile.dart';

/// A single explanatory step for how a move is performed.
sealed class MoveStep {
  const MoveStep();
}

/// Tiles played from the rack onto the table.
final class PlayTilesFromRackStep extends MoveStep {
  const PlayTilesFromRackStep(this.tiles);

  final List<Tile> tiles;
}

/// Table melds were broken apart and rebuilt legally.
final class ReorganizeTableStep extends MoveStep {
  const ReorganizeTableStep({
    required this.meldsBeforeCount,
    required this.meldsAfterCount,
  });

  final int meldsBeforeCount;
  final int meldsAfterCount;
}
