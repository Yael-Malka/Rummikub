import 'meld_type.dart';
import 'tile.dart';

/// A valid set on the table: same-number group or same-color run.
final class Meld {
  const Meld({
    required this.type,
    required this.tiles,
  }) : assert(tiles.length >= 3);

  final MeldType type;
  final List<Tile> tiles;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Meld && type == other.type && _tilesEqual(other.tiles);

  @override
  int get hashCode => Object.hash(type, Object.hashAll(tiles));

  bool _tilesEqual(List<Tile> otherTiles) {
    if (tiles.length != otherTiles.length) {
      return false;
    }
    for (var i = 0; i < tiles.length; i++) {
      if (tiles[i] != otherTiles[i]) {
        return false;
      }
    }
    return true;
  }
}
