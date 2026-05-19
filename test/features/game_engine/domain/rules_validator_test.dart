import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/core/constants/rules_constants.dart';
import 'package:rummikub_app/features/game_engine/domain/rules_validator.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('RulesValidator.validateMeld — group', () {
    test('givenThreeDifferentColorsSameNumber_whenGroup_thenValid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 8),
          regularTile(TileColor.blue, 8),
          regularTile(TileColor.black, 8),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isTrue);
    });

    test('givenFourDifferentColors_whenGroup_thenValid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 5),
          regularTile(TileColor.blue, 5),
          regularTile(TileColor.black, 5),
          regularTile(TileColor.orange, 5),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isTrue);
    });

    test('givenDuplicateColor_whenGroup_thenInvalid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 8),
          regularTile(TileColor.red, 8, copyIndex: 1),
          regularTile(TileColor.blue, 8),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });

    test('givenDifferentNumbers_whenGroup_thenInvalid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 8),
          regularTile(TileColor.blue, 9),
          regularTile(TileColor.black, 8),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });

    test('givenJokerInGroup_whenGroup_thenValid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 10),
          regularTile(TileColor.blue, 10),
          jokerTile(),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isTrue);
    });

  });

  group('RulesValidator.validateMeld — run', () {
    test('givenConsecutiveSameColor_whenRun_thenValid', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.red, 3),
          regularTile(TileColor.red, 4),
          regularTile(TileColor.red, 5),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isTrue);
    });

    test('givenGapFilledByJoker_whenRun_thenValid', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.blue, 3),
          jokerTile(),
          regularTile(TileColor.blue, 5),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isTrue);
    });

    test('givenNonConsecutive_whenRun_thenInvalid', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.red, 3),
          regularTile(TileColor.red, 5),
          regularTile(TileColor.red, 7),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });

    test('givenWrapAround13To1_whenRun_thenInvalid', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.orange, 12),
          regularTile(TileColor.orange, 13),
          regularTile(TileColor.orange, 1),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });

    test('givenMixedColors_whenRun_thenInvalid', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.red, 6),
          regularTile(TileColor.blue, 7),
          regularTile(TileColor.red, 8),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });

    test('givenValidRunButGroupType_whenValidated_thenInvalid', () {
      final meld = Meld(
        type: MeldType.group,
        tiles: [
          regularTile(TileColor.red, 3),
          regularTile(TileColor.red, 4),
          regularTile(TileColor.red, 5),
        ],
      );

      expect(RulesValidator.validateMeld(meld).isValid, isFalse);
    });
  });

  group('RulesValidator.validateGameState', () {
    test('givenValidTableAndRack_whenValidated_thenSuccess', () {
      final t1 = regularTile(TileColor.red, 1);
      final t2 = regularTile(TileColor.blue, 1);
      final t3 = regularTile(TileColor.black, 1);
      final rackTile = regularTile(TileColor.orange, 9);

      final state = GameState(
        rack: [rackTile],
        tableMelds: [
          Meld(type: MeldType.group, tiles: [t1, t2, t3]),
        ],
      );

      expect(RulesValidator.validateGameState(state).isValid, isTrue);
    });

    test('givenDuplicateTileInRackAndTable_whenValidated_thenFails', () {
      final shared = regularTile(TileColor.red, 7);
      final state = GameState(
        rack: [shared],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              shared,
              regularTile(TileColor.blue, 7),
              regularTile(TileColor.black, 7),
            ],
          ),
        ],
      );

      expect(RulesValidator.validateGameState(state).isValid, isFalse);
    });
  });

  group('RulesValidator scoring', () {
    test('givenNumberTiles_whenScored_thenSumOfValues', () {
      final score = RulesValidator.scoreTilesFromRack([
        regularTile(TileColor.red, 10),
        regularTile(TileColor.blue, 11),
      ]);

      expect(score, 21);
    });

    test('givenJokerFromRack_whenScored_then30Points', () {
      final score = RulesValidator.scoreTilesFromRack([jokerTile()]);

      expect(score, RulesConstants.jokerPointValue);
    });

    test('given30Points_whenInitialMeldCheck_thenMeetsRequirement', () {
      expect(RulesValidator.meetsInitialMeldRequirement(30), isTrue);
      expect(RulesValidator.meetsInitialMeldRequirement(29), isFalse);
    });
  });
}
