import 'meld.dart';
import 'tile.dart';
import 'tile_id.dart';

/// Player rack + table melds visible in the current turn.
final class GameState {
  const GameState({
    required this.rack,
    required this.tableMelds,
  });

  final List<Tile> rack;
  final List<Meld> tableMelds;

  /// All tiles currently in this state (rack + table).
  List<Tile> get allTiles => [
        ...rack,
        for (final meld in tableMelds) ...meld.tiles,
      ];

  /// Unique tile identities used in this state.
  Set<TileId> get usedTileIds => allTiles.map((t) => t.id).toSet();

  int get rackSize => rack.length;

  int get tableTileCount =>
      tableMelds.fold<int>(0, (sum, meld) => sum + meld.tiles.length);

  GameState copyWith({
    List<Tile>? rack,
    List<Meld>? tableMelds,
  }) {
    return GameState(
      rack: rack ?? this.rack,
      tableMelds: tableMelds ?? this.tableMelds,
    );
  }
}
