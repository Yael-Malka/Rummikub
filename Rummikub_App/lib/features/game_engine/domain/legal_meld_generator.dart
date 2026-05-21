import '../../../core/constants/deck_constants.dart';
import '../../../core/constants/rules_constants.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/meld_type.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_color.dart';
import 'rules_validator.dart';

/// Every legal meld that can be built from [pool] (table + rack tiles).
///
/// Each meld uses a given tile at most once.
abstract final class LegalMeldGenerator {
  static List<Meld> generateCandidates(List<Tile> pool) {
    if (pool.length < RulesConstants.minMeldLength) {
      return const [];
    }

    final results = <Meld>[];
    final alreadySeen = <String>{};

    void rememberIfValid(Meld meld) {
      if (!RulesValidator.validateMeld(meld).isValid) {
        return;
      }
      final signature = _signatureFor(meld);
      if (alreadySeen.add(signature)) {
        results.add(meld);
      }
    }

    final jokers = pool.where((t) => t.isJoker).toList();
    final tilesByNumber = <int, List<Tile>>{};
    final tilesByColor = <TileColor, List<Tile>>{};

    for (final tile in pool) {
      if (tile.isJoker) {
        continue;
      }
      tilesByNumber.putIfAbsent(tile.number!, () => []).add(tile);
      tilesByColor.putIfAbsent(tile.color!, () => []).add(tile);
    }

    emitAllGroups(tilesByNumber, jokers, rememberIfValid);
    emitAllRuns(tilesByColor, jokers, rememberIfValid);

    // Small pools: brute-force combinations so we do not miss edge cases.
    if (pool.length <= 20) {
      emitFromRawCombinations(pool, rememberIfValid);
    }

    return results;
  }

  static void emitAllGroups(
    Map<int, List<Tile>> tilesByNumber,
    List<Tile> jokers,
    void Function(Meld meld) remember,
  ) {
    for (final entry in tilesByNumber.entries) {
      final sameNumber = entry.value;
      final byColor = <TileColor, List<Tile>>{};
      for (final tile in sameNumber) {
        byColor.putIfAbsent(tile.color!, () => []).add(tile);
      }

      final availableColors = byColor.keys.toList();
      if (availableColors.length + jokers.length < RulesConstants.minMeldLength) {
        continue;
      }

      for (var groupSize = RulesConstants.minMeldLength;
          groupSize <= RulesConstants.maxGroupLength;
          groupSize++) {
        for (final colorPick in combinationsOf(availableColors, groupSize)) {
          buildGroupFromColors(colorPick, byColor, jokers, remember);
        }
        if (groupSize > availableColors.length) {
          buildGroupWithJokers(
            availableColors,
            byColor,
            jokers,
            groupSize,
            remember,
          );
        }
      }
    }
  }

  static void buildGroupFromColors(
    List<TileColor> colors,
    Map<TileColor, List<Tile>> byColor,
    List<Tile> jokers,
    void Function(Meld meld) remember,
  ) {
    final tiles = <Tile>[
      for (final color in colors) byColor[color]!.first,
    ];
    remember(Meld(type: MeldType.group, tiles: List.unmodifiable(tiles)));

    // Two physical copies of the same color/number — try the second copy too.
    for (final color in colors) {
      final copies = byColor[color]!;
      if (copies.length < 2) {
        continue;
      }
      final withSecondCopy = [
        for (final c in colors) c == color ? copies[1] : byColor[c]!.first,
      ];
      remember(
        Meld(type: MeldType.group, tiles: List.unmodifiable(withSecondCopy)),
      );
    }
  }

  static void buildGroupWithJokers(
    List<TileColor> colors,
    Map<TileColor, List<Tile>> byColor,
    List<Tile> jokers,
    int groupSize,
    void Function(Meld meld) remember,
  ) {
    final jokersNeeded = groupSize - colors.length;
    if (jokersNeeded <= 0 || jokersNeeded > jokers.length) {
      return;
    }

    final colorCount = groupSize - jokersNeeded;
    for (final colorPick in combinationsOf(colors, colorCount)) {
      if (colorPick.length != colorCount) {
        continue;
      }
      for (final jokerPick in combinationsOf(
        List.generate(jokers.length, (i) => i),
        jokersNeeded,
      )) {
        final tiles = [
          for (final color in colorPick) byColor[color]!.first,
          for (final j in jokerPick) jokers[j],
        ];
        if (tiles.length == groupSize) {
          remember(Meld(type: MeldType.group, tiles: List.unmodifiable(tiles)));
        }
      }
    }
  }

  static void emitAllRuns(
    Map<TileColor, List<Tile>> tilesByColor,
    List<Tile> jokers,
    void Function(Meld meld) remember,
  ) {
    for (final entry in tilesByColor.entries) {
      final byNumber = <int, List<Tile>>{};
      for (final tile in entry.value) {
        byNumber.putIfAbsent(tile.number!, () => []).add(tile);
      }

      for (var runStart = DeckConstants.minNumber;
          runStart <= DeckConstants.maxNumber;
          runStart++) {
        for (var runLength = RulesConstants.minMeldLength;
            runLength <= DeckConstants.maxNumber;
            runLength++) {
          final runEnd = runStart + runLength - 1;
          if (runEnd > DeckConstants.maxNumber) {
            break;
          }

          final numbersInRun = [
            for (var n = runStart; n <= runEnd; n++) n,
          ];

          fillRunWithTiles(
            numbersInRun,
            position: 0,
            tilesByNumber: byNumber,
            jokers: jokers,
            pickedSoFar: [],
            usedJokerSlots: {},
            remember: remember,
          );
        }
      }
    }
  }

  /// Walks consecutive numbers; each slot is a real tile or a joker.
  static void fillRunWithTiles(
    List<int> numbersInRun, {
    required int position,
    required Map<int, List<Tile>> tilesByNumber,
    required List<Tile> jokers,
    required List<Tile> pickedSoFar,
    required Set<int> usedJokerSlots,
    required void Function(Meld meld) remember,
  }) {
    if (position == numbersInRun.length) {
      remember(Meld(type: MeldType.run, tiles: List.unmodifiable(pickedSoFar)));
      return;
    }

    final number = numbersInRun[position];
    final copies = tilesByNumber[number];
    if (copies != null) {
      for (final tile in copies) {
        if (pickedSoFar.any((t) => t.id == tile.id)) {
          continue;
        }
        pickedSoFar.add(tile);
        fillRunWithTiles(
          numbersInRun,
          position: position + 1,
          tilesByNumber: tilesByNumber,
          jokers: jokers,
          pickedSoFar: pickedSoFar,
          usedJokerSlots: usedJokerSlots,
          remember: remember,
        );
        pickedSoFar.removeLast();
      }
    }

    for (var j = 0; j < jokers.length; j++) {
      if (usedJokerSlots.contains(j)) {
        continue;
      }
      usedJokerSlots.add(j);
      pickedSoFar.add(jokers[j]);
      fillRunWithTiles(
        numbersInRun,
        position: position + 1,
        tilesByNumber: tilesByNumber,
        jokers: jokers,
        pickedSoFar: pickedSoFar,
        usedJokerSlots: usedJokerSlots,
        remember: remember,
      );
      pickedSoFar.removeLast();
      usedJokerSlots.remove(j);
    }
  }

  /// Fallback: every 3+ subset of the pool, checked as group and as run.
  static void emitFromRawCombinations(
    List<Tile> pool,
    void Function(Meld meld) remember,
  ) {
    final n = pool.length;
    for (var size = RulesConstants.minMeldLength; size <= n; size++) {
      for (final indices in combinationsOf(List.generate(n, (i) => i), size)) {
        final tiles = [for (final i in indices) pool[i]];
        remember(Meld(type: MeldType.group, tiles: tiles));
        remember(Meld(type: MeldType.run, tiles: tiles));
      }
    }
  }

  static Iterable<List<T>> combinationsOf<T>(List<T> items, int size) sync* {
    if (size < 0 || size > items.length) {
      return;
    }
    if (size == 0) {
      yield [];
      return;
    }

    Iterable<List<T>> pickFrom(int start, List<T> current) sync* {
      if (current.length == size) {
        yield List.unmodifiable(current);
        return;
      }
      for (var i = start; i <= items.length - (size - current.length); i++) {
        current.add(items[i]);
        yield* pickFrom(i + 1, current);
        current.removeLast();
      }
    }

    yield* pickFrom(0, []);
  }

  static String _signatureFor(Meld meld) {
    final ids = meld.tiles.map((t) => t.id.hashCode).toList()..sort();
    return '${meld.type.name}:${ids.join('|')}';
  }
}
