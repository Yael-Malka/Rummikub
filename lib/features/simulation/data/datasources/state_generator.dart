import 'dart:math';

import '../../../../core/constants/simulation_constants.dart';
import '../../../game_engine/domain/full_deck.dart';
import '../../../game_engine/domain/rules_validator.dart';
import '../../domain/entities/game_state.dart';
import '../../domain/entities/meld.dart';
import '../../domain/entities/meld_type.dart';
import '../../domain/entities/tile.dart';
import '../../domain/entities/tile_color.dart';
import '../../domain/exceptions/state_generation_exception.dart';

/// Builds random rack + table states from the full deck.
final class StateGenerator {
  StateGenerator({Random? random}) : _random = random ?? Random();

  final Random _random;

  static const List<TileColor> _playColors = [
    TileColor.red,
    TileColor.blue,
    TileColor.black,
    TileColor.orange,
  ];

  GameState generate({bool emptyTable = false}) {
    for (var attempt = 0;
        attempt < SimulationConstants.maxGenerationAttempts;
        attempt++) {
      final state = _tryGenerateOnce(emptyTable: emptyTable);
      if (RulesValidator.validateGameState(state).isValid) {
        return state;
      }
    }

    throw const StateGenerationException(
      'Could not build a valid simulated state',
    );
  }

  GameState _tryGenerateOnce({required bool emptyTable}) {
    final pool = List<Tile>.from(FullDeck.create())..shuffle(_random);

    final tableMelds = <Meld>[];
    if (!emptyTable) {
      final meldCount = SimulationConstants.minTableMelds +
          _random.nextInt(
            SimulationConstants.maxTableMelds -
                SimulationConstants.minTableMelds +
                1,
          );

      for (var i = 0; i < meldCount; i++) {
        final meld = _random.nextBool()
            ? _tryBuildGroup(pool)
            : _tryBuildRun(pool);
        if (meld == null) {
          break;
        }
        tableMelds.add(meld);
      }

      if (tableMelds.isEmpty) {
        final fallback = _tryBuildGroup(pool) ?? _tryBuildRun(pool);
        if (fallback != null) {
          tableMelds.add(fallback);
        }
      }
    }

    final rackSize = _pickRackSize(pool.length);
    final rack = pool.take(rackSize).toList();
    pool.removeRange(0, rack.length.clamp(0, pool.length));

    return GameState(rack: rack, tableMelds: tableMelds);
  }

  int _pickRackSize(int tilesLeftInPool) {
    const minSize = SimulationConstants.minRackSize;
    const maxSize = SimulationConstants.maxRackSize;
    final cappedMax = min(maxSize, tilesLeftInPool);
    if (cappedMax < minSize) {
      return cappedMax;
    }
    return minSize + _random.nextInt(cappedMax - minSize + 1);
  }

  Meld? _tryBuildGroup(List<Tile> pool) {
    final byNumber = <int, List<Tile>>{};
    for (final tile in pool) {
      if (tile.isJoker) {
        continue;
      }
      byNumber.putIfAbsent(tile.number!, () => []).add(tile);
    }

    if (byNumber.isEmpty) {
      return null;
    }

    final candidates = byNumber.entries
        .where((e) => _distinctColors(e.value) >= 3)
        .toList();
    if (candidates.isEmpty) {
      return null;
    }

    final entry = candidates[_random.nextInt(candidates.length)];
    final colorBuckets = <TileColor, List<Tile>>{};
    for (final tile in entry.value) {
      colorBuckets.putIfAbsent(tile.color!, () => []).add(tile);
    }

    final availableColors = colorBuckets.keys.toList()..shuffle(_random);
    final maxLen = min(4, availableColors.length);
    final length = 3 + _random.nextInt(maxLen - 3 + 1);

    final picked = <Tile>[];
    for (var i = 0; i < length; i++) {
      final color = availableColors[i];
      picked.add(colorBuckets[color]!.first);
    }

    final jokers = pool.where((t) => t.isJoker).toList();
    while (picked.length < 3 && jokers.isNotEmpty) {
      final joker = jokers.removeAt(0);
      picked.add(joker);
      pool.remove(joker);
    }

    if (picked.length < 3) {
      return null;
    }

    for (final tile in picked) {
      pool.remove(tile);
    }

    return Meld(type: MeldType.group, tiles: picked);
  }

  Meld? _tryBuildRun(List<Tile> pool) {
    for (var attempt = 0; attempt < 8; attempt++) {
      final color = _playColors[_random.nextInt(_playColors.length)];
      final length = 3 + _random.nextInt(3);
      final maxStart = 13 - length + 1;
      if (maxStart < 1) {
        continue;
      }
      final start = 1 + _random.nextInt(maxStart);

      final picked = <Tile>[];
      var jokers = pool.where((t) => t.isJoker).toList();

      for (var n = start; n < start + length; n++) {
        final match = pool.where(
          (t) => !t.isJoker && t.color == color && t.number == n,
        );
        if (match.isNotEmpty) {
          picked.add(match.first);
        } else if (jokers.isNotEmpty) {
          final joker = jokers.first;
          picked.add(joker);
          jokers = jokers.sublist(1);
        } else {
          picked.clear();
          break;
        }
      }

      if (picked.length < 3) {
        continue;
      }

      final meld = Meld(type: MeldType.run, tiles: picked);
      if (!RulesValidator.validateMeld(meld).isValid) {
        continue;
      }

      for (final tile in picked) {
        pool.remove(tile);
      }
      return meld;
    }

    return null;
  }

  int _distinctColors(List<Tile> tiles) {
    return tiles.map((t) => t.color).toSet().length;
  }
}
