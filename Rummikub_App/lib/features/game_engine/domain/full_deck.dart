import '../../../core/constants/deck_constants.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_color.dart';
import '../../simulation/domain/entities/tile_id.dart';

/// Builds and validates the standard 106-tile Rummikub deck.
abstract final class FullDeck {
  static const int tileCount = DeckConstants.tileCount;

  static final List<TileColor> _playColors = [
    TileColor.red,
    TileColor.blue,
    TileColor.black,
    TileColor.orange,
  ];

  /// Creates a new full deck in deterministic order.
  static List<Tile> create() {
    final tiles = <Tile>[];

    for (final color in _playColors) {
      for (var number = DeckConstants.minNumber;
          number <= DeckConstants.maxNumber;
          number++) {
        for (var copy = 0; copy < DeckConstants.copiesPerNumber; copy++) {
          tiles.add(
            Tile(
              id: RegularTileId(
                color: color,
                number: number,
                copyIndex: copy,
              ),
            ),
          );
        }
      }
    }

    for (var j = 0; j < DeckConstants.jokerCount; j++) {
      tiles.add(Tile(id: JokerTileId(copyIndex: j)));
    }

    return List.unmodifiable(tiles);
  }

  /// Returns true if [tiles] has exactly 106 unique physical identities.
  static bool hasUniqueIds(Iterable<Tile> tiles) {
    final ids = <TileId>{};
    for (final tile in tiles) {
      if (!ids.add(tile.id)) {
        return false;
      }
    }
    return true;
  }

  /// Count of tiles matching [color] and [number] in [tiles].
  static int countRegular(
    Iterable<Tile> tiles, {
    required TileColor color,
    required int number,
  }) {
    return tiles
        .where(
          (t) =>
              t.id is RegularTileId &&
              t.color == color &&
              t.number == number,
        )
        .length;
  }
}
