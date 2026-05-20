import '../../../simulation/domain/entities/game_state.dart';
import '../../../simulation/domain/entities/meld.dart';
import '../../../simulation/domain/entities/tile.dart';

/// A legal end-of-turn result after playing tiles from the rack.
final class Move {
  const Move({
    required this.tilesPlayedFromRack,
    required this.finalTableMelds,
    required this.finalRack,
  });

  final int tilesPlayedFromRack;
  final List<Meld> finalTableMelds;
  final List<Tile> finalRack;

  GameState toGameState() {
    return GameState(
      rack: finalRack,
      tableMelds: finalTableMelds,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is Move &&
            tilesPlayedFromRack == other.tilesPlayedFromRack &&
            _sameTiles(finalRack, other.finalRack) &&
            _sameMelds(finalTableMelds, other.finalTableMelds);
  }

  @override
  int get hashCode => Object.hash(
        tilesPlayedFromRack,
        Object.hashAll(finalRack.map((t) => t.id)),
        Object.hashAll(finalTableMelds),
      );

  static bool _sameTiles(List<Tile> a, List<Tile> b) {
    if (a.length != b.length) {
      return false;
    }
    final idsA = a.map((t) => t.id).toSet();
    return idsA.length == b.length && b.every((t) => idsA.contains(t.id));
  }

  static bool _sameMelds(List<Meld> a, List<Meld> b) {
    if (a.length != b.length) {
      return false;
    }
    final sortedA = [...a]..sort((x, y) => _meldKey(x).compareTo(_meldKey(y)));
    final sortedB = [...b]..sort((x, y) => _meldKey(x).compareTo(_meldKey(y)));
    for (var i = 0; i < sortedA.length; i++) {
      if (sortedA[i] != sortedB[i]) {
        return false;
      }
    }
    return true;
  }

  static String _meldKey(Meld meld) {
    final ids = meld.tiles.map((t) => t.id.hashCode).toList()..sort();
    return '${meld.type.name}:${ids.join(',')}';
  }
}
