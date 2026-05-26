import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/meld_type.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_color.dart';
import 'rules_validator.dart';

/// Fast path: extend existing table melds with rack tiles (no full re-partition).
abstract final class TableExtensionSolver {
  /// All ways to attach [playedFromRack] to current [tableMelds] in place.
  static List<List<Meld>> findExtendedLayouts(
    List<Meld> tableMelds,
    List<Tile> playedFromRack,
  ) {
    if (playedFromRack.isEmpty) {
      return [List.unmodifiable(tableMelds)];
    }
    if (tableMelds.isEmpty) {
      return const [];
    }

    final results = <List<Meld>>[];
    final seen = <String>{};
    final additions = List<List<Tile>>.generate(
      tableMelds.length,
      (_) => <Tile>[],
    );

    void search(int playedIndex) {
      if (playedIndex == playedFromRack.length) {
        final built = _buildMelds(tableMelds, additions);
        if (built != null) {
          final key = _layoutKey(built);
          if (seen.add(key)) {
            results.add(built);
          }
        }
        return;
      }

      final tile = playedFromRack[playedIndex];
      for (var meldIndex = 0; meldIndex < tableMelds.length; meldIndex++) {
        if (!_canAddToMeld(tableMelds[meldIndex], additions[meldIndex], tile)) {
          continue;
        }
        additions[meldIndex].add(tile);
        search(playedIndex + 1);
        additions[meldIndex].removeLast();
      }
    }

    search(0);
    return results;
  }

  static bool _canAddToMeld(Meld meld, List<Tile> pending, Tile tile) {
    if (tile.isJoker) {
      return _validateCombined(meld.type, [...meld.tiles, ...pending, tile]);
    }

    return switch (meld.type) {
      MeldType.run => tile.color == _runColor(meld, pending),
      MeldType.group => _groupNumber(meld, pending) == tile.number,
    };
  }

  static TileColor? _runColor(Meld meld, List<Tile> pending) {
    for (final tile in [...meld.tiles, ...pending]) {
      if (!tile.isJoker && tile.color != null) {
        return tile.color;
      }
    }
    return null;
  }

  static int? _groupNumber(Meld meld, List<Tile> pending) {
    for (final tile in [...meld.tiles, ...pending]) {
      if (!tile.isJoker) {
        return tile.number;
      }
    }
    return null;
  }

  static bool _validateCombined(MeldType type, List<Tile> tiles) {
    return RulesValidator.validateMeld(Meld(type: type, tiles: tiles)).isValid;
  }

  static List<Meld>? _buildMelds(
    List<Meld> tableMelds,
    List<List<Tile>> additions,
  ) {
    final built = <Meld>[];
    for (var i = 0; i < tableMelds.length; i++) {
      if (additions[i].isEmpty) {
        built.add(tableMelds[i]);
        continue;
      }
      final combined = [...tableMelds[i].tiles, ...additions[i]];
      final meld = Meld(type: tableMelds[i].type, tiles: combined);
      if (!RulesValidator.validateMeld(meld).isValid) {
        return null;
      }
      built.add(meld);
    }
    return built;
  }

  static String _layoutKey(List<Meld> melds) {
    final parts = melds.map((meld) {
      final ids = meld.tiles.map((t) => t.id.hashCode).toList()..sort();
      return '${meld.type.name}:${ids.join(',')}';
    }).toList()
      ..sort();
    return parts.join('|');
  }
}
