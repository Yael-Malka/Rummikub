import '../../../core/constants/rules_constants.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/meld_type.dart';
import '../../simulation/domain/entities/tile.dart';
import 'rules_validator.dart';

/// Finds ways to split tiles into valid Rummikub melds.
abstract final class MeldPartitioner {
  static List<List<Meld>> findAllPartitions(
    List<Tile> tiles, {
    int maxResults = 32,
  }) {
    if (tiles.isEmpty) {
      return [[]];
    }

    final sorted = List<Tile>.from(tiles)
      ..sort((a, b) => a.id.hashCode.compareTo(b.id.hashCode));

    final results = <List<Meld>>[];
    final seen = <String>{};

    void backtrack(List<Tile> remaining, List<Meld> built) {
      if (results.length >= maxResults) {
        return;
      }

      if (remaining.isEmpty) {
        final key = _partitionKey(built);
        if (seen.add(key)) {
          results.add(List.unmodifiable(built.map(_copyMeld)));
        }
        return;
      }

      for (final meld in _candidateMelds(remaining)) {
        final nextRemaining = _removeTiles(remaining, meld.tiles);
        if (nextRemaining.length != remaining.length - meld.tiles.length) {
          continue;
        }
        built.add(meld);
        backtrack(nextRemaining, built);
        built.removeLast();
      }
    }

    backtrack(sorted, []);
    return results;
  }

  static List<Meld> _candidateMelds(List<Tile> tiles) {
    final candidates = <Meld>[];
    final seen = <String>{};

    void addMeld(Meld meld) {
      if (RulesValidator.validateMeld(meld).isValid) {
        final key = _meldKey(meld);
        if (seen.add(key)) {
          candidates.add(meld);
        }
      }
    }

    final n = tiles.length;
    for (var size = RulesConstants.minMeldLength; size <= n; size++) {
      for (final combo in _combinations(tiles, size)) {
        addMeld(Meld(type: MeldType.group, tiles: combo));
        addMeld(Meld(type: MeldType.run, tiles: combo));
      }
    }

    return candidates;
  }

  static List<List<Tile>> _combinations(List<Tile> tiles, int size) {
    final results = <List<Tile>>[];

    void choose(int start, List<Tile> picked) {
      if (picked.length == size) {
        results.add(List.unmodifiable(picked));
        return;
      }
      for (var i = start; i <= tiles.length - (size - picked.length); i++) {
        picked.add(tiles[i]);
        choose(i + 1, picked);
        picked.removeLast();
      }
    }

    choose(0, []);
    return results;
  }

  static List<Tile> _removeTiles(List<Tile> from, List<Tile> remove) {
    final removeIds = remove.map((t) => t.id).toSet();
    return from.where((t) => !removeIds.contains(t.id)).toList();
  }

  static Meld _copyMeld(Meld meld) {
    return Meld(type: meld.type, tiles: List.unmodifiable(meld.tiles));
  }

  static String _meldKey(Meld meld) {
    final ids = meld.tiles.map((t) => t.id.hashCode).toList()..sort();
    return '${meld.type.name}:${ids.join('|')}';
  }

  static String _partitionKey(List<Meld> melds) {
    final keys = melds.map(_meldKey).toList()..sort();
    return keys.join(';');
  }
}
