import '../../../core/constants/deck_constants.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/meld_type.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_color.dart';
import '../../simulation/domain/entities/tile_id.dart';
import 'entities/move_explanation.dart';
import 'rules_validator.dart';

/// Infers what each joker represents inside a valid meld.
abstract final class JokerRoleInferrer {
  static List<JokerRole> forMeld(Meld meld) {
    final jokers = meld.tiles.where((t) => t.isJoker).toList();
    if (jokers.isEmpty) {
      return const [];
    }

    if (!RulesValidator.validateMeld(meld).isValid) {
      return const [];
    }

    return switch (meld.type) {
      MeldType.group => _rolesInGroup(meld, jokers),
      MeldType.run => _rolesInRun(meld, jokers),
    };
  }

  static List<JokerRole> _rolesInGroup(Meld meld, List<Tile> jokers) {
    final regular = meld.tiles.where((t) => !t.isJoker).toList();
    if (regular.isEmpty) {
      return const [];
    }

    final number = regular.first.number!;
    final usedColors = regular.map((t) => t.color!).toSet();
    final missingColors = TileColor.values
        .where((c) => c != TileColor.joker && !usedColors.contains(c))
        .toList();

    if (missingColors.length < jokers.length) {
      return const [];
    }

    return [
      for (var i = 0; i < jokers.length; i++)
        JokerRole(
          jokerTileId: jokers[i].id,
          standsInForNumber: number,
          standsInForColor: missingColors[i],
        ),
    ];
  }

  static List<JokerRole> _rolesInRun(Meld meld, List<Tile> jokers) {
    final regular = meld.tiles.where((t) => !t.isJoker).toList();
    if (regular.isEmpty) {
      return const [];
    }

    final color = regular.first.color!;
    final numbers = regular.map((t) => t.number!).toList()..sort();
    final span = _findRunSpan(numbers, jokers.length, meld.tiles.length);
    if (span == null) {
      return const [];
    }

    final (start, end) = span;
    final present = numbers.toSet();
    final missingNumbers = <int>[];
    for (var n = start; n <= end; n++) {
      if (!present.contains(n)) {
        missingNumbers.add(n);
      }
    }

    if (missingNumbers.length != jokers.length) {
      return const [];
    }

    return [
      for (var i = 0; i < jokers.length; i++)
        JokerRole(
          jokerTileId: jokers[i].id,
          standsInForNumber: missingNumbers[i],
          standsInForColor: color,
        ),
    ];
  }

  static (int, int)? _findRunSpan(
    List<int> fixedNumbers,
    int jokerCount,
    int totalLength,
  ) {
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
      if (needed.length == jokerCount) {
        return (start, end);
      }
    }
    return null;
  }
}
