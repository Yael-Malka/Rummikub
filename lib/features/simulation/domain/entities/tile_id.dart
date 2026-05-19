import 'tile_color.dart';

/// Unique identity of a physical tile in the 106-tile deck.
sealed class TileId {
  const TileId();
}

/// Numbered tile: one of two copies per (color, number).
final class RegularTileId extends TileId {
  const RegularTileId({
    required this.color,
    required this.number,
    required this.copyIndex,
  })  : assert(number >= 1 && number <= 13),
        assert(copyIndex == 0 || copyIndex == 1),
        assert(color != TileColor.joker);

  final TileColor color;
  final int number;
  final int copyIndex;

  @override
  bool operator ==(Object other) {
    return other is RegularTileId &&
        color == other.color &&
        number == other.number &&
        copyIndex == other.copyIndex;
  }

  @override
  int get hashCode => Object.hash(color, number, copyIndex);
}

/// Joker tile: one of two jokers in the deck.
final class JokerTileId extends TileId {
  const JokerTileId({required this.copyIndex})
      : assert(copyIndex == 0 || copyIndex == 1);

  final int copyIndex;

  @override
  bool operator ==(Object other) {
    return other is JokerTileId && copyIndex == other.copyIndex;
  }

  @override
  int get hashCode => copyIndex;
}
