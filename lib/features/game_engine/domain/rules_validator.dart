import '../../../core/constants/deck_constants.dart';
import '../../../core/constants/rules_constants.dart';
import '../../simulation/domain/entities/game_state.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/meld_type.dart';
import '../../simulation/domain/entities/tile.dart';
import 'full_deck.dart';
import 'validation_result.dart';

/// Validates Rummikub melds and game states against official rules.
abstract final class RulesValidator {
  static ValidationResult validateMeld(Meld meld) {
    if (meld.tiles.length < RulesConstants.minMeldLength) {
      return const ValidationFailure(
        'Meld must have at least 3 tiles',
      );
    }

    final isGroup = _isValidGroup(meld.tiles);
    final isRun = _isValidRun(meld.tiles);

    return switch (meld.type) {
      MeldType.group when isGroup => const ValidationSuccess(),
      MeldType.group => const ValidationFailure('Invalid group meld'),
      MeldType.run when isRun => const ValidationSuccess(),
      MeldType.run => const ValidationFailure('Invalid run meld'),
    };
  }

  static ValidationResult validateGameState(GameState state) {
    if (!FullDeck.hasUniqueIds(state.allTiles)) {
      return const ValidationFailure('Duplicate tile in game state');
    }

    if (!_isWithinDeckLimits(state.allTiles)) {
      return const ValidationFailure('Tile count exceeds deck limits');
    }

    for (final meld in state.tableMelds) {
      final result = validateMeld(meld);
      if (!result.isValid) {
        return ValidationFailure(
          'Invalid table meld: ${result.message}',
        );
      }
    }

    return const ValidationSuccess();
  }

  /// Point value of tiles played from the rack (opening-meld scoring).
  static int scoreTilesFromRack(Iterable<Tile> tiles) {
    var total = 0;
    for (final tile in tiles) {
      total += tilePointValue(tile);
    }
    return total;
  }

  static int tilePointValue(Tile tile) {
    if (tile.isJoker) {
      return RulesConstants.jokerPointValue;
    }
    return tile.number ?? 0;
  }

  static bool meetsInitialMeldRequirement(int pointsFromRack) {
    return pointsFromRack >= RulesConstants.initialMeldMinimumPoints;
  }

  /// First meld: at least one rack tile played and 30+ points from those tiles.
  static bool satisfiesFirstMeldPlay(Iterable<Tile> rackTilesPlayed) {
    final played = rackTilesPlayed.toList();
    if (played.isEmpty) {
      return false;
    }
    return meetsInitialMeldRequirement(scoreTilesFromRack(played));
  }

  static bool _isValidGroup(List<Tile> tiles) {
    if (tiles.length < RulesConstants.minMeldLength ||
        tiles.length > RulesConstants.maxGroupLength) {
      return false;
    }

    final regular = tiles.where((t) => !t.isJoker).toList();
    if (regular.isEmpty) {
      return false;
    }

    final number = regular.first.number;
    if (regular.any((t) => t.number != number)) {
      return false;
    }

    final colors = regular.map((t) => t.color).toSet();
    return colors.length == regular.length;
  }

  static bool _isValidRun(List<Tile> tiles) {
    if (tiles.length < RulesConstants.minMeldLength) {
      return false;
    }

    final jokerCount = tiles.where((t) => t.isJoker).length;
    final regular = tiles.where((t) => !t.isJoker).toList();
    if (regular.isEmpty) {
      return false;
    }

    final color = regular.first.color;
    if (regular.any((t) => t.color != color)) {
      return false;
    }

    final numbers = regular.map((t) => t.number!).toList();
    if (numbers.toSet().length != numbers.length) {
      return false;
    }

    return _canFormConsecutiveRun(numbers, jokerCount, tiles.length);
  }

  /// Whether [fixedNumbers] + [jokerCount] can form a consecutive run of [totalLength].
  static bool _canFormConsecutiveRun(
    List<int> fixedNumbers,
    int jokerCount,
    int totalLength,
  ) {
    if (totalLength > DeckConstants.maxNumber) {
      return false;
    }

    fixedNumbers.sort();
    final minStart = fixedNumbers.last - totalLength + 1;
    final maxStart = fixedNumbers.first;

    for (var start = minStart; start <= maxStart; start++) {
      if (start < DeckConstants.minNumber) {
        continue;
      }
      final end = start + totalLength - 1;
      if (end > DeckConstants.maxNumber) {
        continue;
      }

      final needed = <int>{};
      for (var n = start; n <= end; n++) {
        needed.add(n);
      }

      for (final n in fixedNumbers) {
        needed.remove(n);
      }

      if (needed.length <= jokerCount) {
        return true;
      }
    }

    return false;
  }

  /// Ensures no (color, number) appears more than twice — defensive for partial states.
  static bool _isWithinDeckLimits(Iterable<Tile> tiles) {
    final regularCounts = <String, int>{};
    var jokerCount = 0;

    for (final tile in tiles) {
      if (tile.isJoker) {
        jokerCount++;
        continue;
      }
      final key = '${tile.color!.name}-${tile.number}';
      regularCounts[key] = (regularCounts[key] ?? 0) + 1;
      if (regularCounts[key]! > DeckConstants.copiesPerNumber) {
        return false;
      }
    }

    return jokerCount <= DeckConstants.jokerCount;
  }
}
