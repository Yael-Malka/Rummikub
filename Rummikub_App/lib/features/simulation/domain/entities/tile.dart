import 'tile_color.dart';
import 'tile_id.dart';

/// A single Rummikub tile in play.
final class Tile {
  const Tile({required this.id});

  final TileId id;

  bool get isJoker => id is JokerTileId;

  TileColor? get color => switch (id) {
        RegularTileId(:final color) => color,
        JokerTileId() => TileColor.joker,
      };

  int? get number => switch (id) {
        RegularTileId(:final number) => number,
        JokerTileId() => null,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Tile && id == other.id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => switch (id) {
        RegularTileId(:final color, :final number) => '${color.name}-$number',
        JokerTileId() => 'joker',
      };
}
