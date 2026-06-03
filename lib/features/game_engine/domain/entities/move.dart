import '../../../simulation/domain/entities/game_state.dart';
import '../../../simulation/domain/entities/meld.dart';
import '../../../simulation/domain/entities/tile.dart';
import '../../../simulation/domain/entities/tile_id.dart';

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

  /// Fingerprint for deduplicating moves the user sees as identical.
  ///
  /// Uses color+number (not physical [RegularTileId.copyIndex]) so swapping
  /// deck copies of the same tile does not create duplicate UI entries.
  String get canonicalKey {
    final rackKeys = finalRack.map(visualTileKey).toList()..sort();
    final meldKeys = finalTableMelds.map(visualMeldKey).toList()..sort();
    return '$tilesPlayedFromRack|rack:${rackKeys.join(',')}|'
        'melds:${meldKeys.join(';')}';
  }

  /// Table-only layout key (meld grouping as shown in the UI).
  String get tableLayoutKey {
    final meldKeys = finalTableMelds.map(visualMeldKey).toList()..sort();
    return meldKeys.join(';');
  }

  /// End-state key ignoring how tiles are grouped into melds.
  ///
  /// Swapping deck copies or splitting the same tiles into different valid
  /// melds yields the same key — used to avoid duplicate "same move" entries.
  String get visibleOutcomeKey {
    final onTable = <String>[];
    for (final meld in finalTableMelds) {
      onTable.addAll(meld.tiles.map(visualTileKey));
    }
    onTable.sort();
    final onRack = finalRack.map(visualTileKey).toList()..sort();
    return '$tilesPlayedFromRack|t:${onTable.join(',')}|r:${onRack.join(',')}';
  }

  /// Physical-tile meld key (unique deck copy per tile).
  static String meldKey(Meld meld) {
    final tileKeys = meld.tiles.map((t) => tileIdKey(t.id)).toList()..sort();
    return '${meld.type.name}:${tileKeys.join('|')}';
  }

  /// Visual meld key (what the player sees on the table).
  static String visualMeldKey(Meld meld) {
    final tileKeys = meld.tiles.map(visualTileKey).toList()..sort();
    return '${meld.type.name}:${tileKeys.join('|')}';
  }

  static String visualTileKey(Tile tile) {
    return switch (tile.id) {
      RegularTileId(:final color, :final number) => '${color.name}-$number',
      JokerTileId() => 'joker',
    };
  }

  static String tileIdKey(TileId id) {
    return switch (id) {
      RegularTileId(:final color, :final number, :final copyIndex) =>
        '${color.name}-$number-$copyIndex',
      JokerTileId(:final copyIndex) => 'joker-$copyIndex',
    };
  }

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
  int get hashCode => canonicalKey.hashCode;

  static bool _sameTiles(List<Tile> a, List<Tile> b) {
    if (a.length != b.length) {
      return false;
    }
    final keysA = a.map(visualTileKey).toList()..sort();
    final keysB = b.map(visualTileKey).toList()..sort();
    for (var i = 0; i < keysA.length; i++) {
      if (keysA[i] != keysB[i]) {
        return false;
      }
    }
    return true;
  }

  static bool _sameMelds(List<Meld> a, List<Meld> b) {
    if (a.length != b.length) {
      return false;
    }
    final keysA = a.map(visualMeldKey).toList()..sort();
    final keysB = b.map(visualMeldKey).toList()..sort();
    for (var i = 0; i < keysA.length; i++) {
      if (keysA[i] != keysB[i]) {
        return false;
      }
    }
    return true;
  }
}
