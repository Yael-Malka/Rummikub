import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/core/constants/rules_constants.dart';
import 'package:rummikub_app/features/game_engine/domain/move_solver.dart';
import 'package:rummikub_app/features/game_engine/domain/rules_validator.dart';
import 'package:rummikub_app/features/game_engine/domain/usecases/find_optimal_moves_use_case.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  const useCase = FindOptimalMovesUseCase();

  group('MoveSolver', () {
    test('givenRackTileMatchesGroup_whenSolved_thenPlaysAtLeastOne', () {
      final state = GameState(
        rack: [regularTile(TileColor.orange, 8)],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.red, 8),
              regularTile(TileColor.blue, 8),
              regularTile(TileColor.black, 8),
            ],
          ),
        ],
      );

      final moves = useCase(state, isFirstMeldTurn: false).moves;

      expect(moves, isNotEmpty);
      expect(
        moves.map((m) => m.tilesPlayedFromRack).reduce((a, b) => a > b ? a : b),
        1,
      );
    });

    test('givenRunExtensionOnRack_whenSolved_thenPlaysMultipleTiles', () {
      final state = GameState(
        rack: [
          regularTile(TileColor.orange, 8),
          regularTile(TileColor.orange, 9),
        ],
        tableMelds: [
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.orange, 5),
              regularTile(TileColor.orange, 6),
              regularTile(TileColor.orange, 7),
            ],
          ),
        ],
      );

      final moves = useCase(state, isFirstMeldTurn: false).moves;

      expect(moves, isNotEmpty);
      final maxPlayed =
          moves.map((m) => m.tilesPlayedFromRack).reduce((a, b) => a > b ? a : b);
      expect(maxPlayed, 2);
    });

    test('givenFirstMeldBelow30_whenSolved_thenNoMovesOrOnlyValidOnes', () {
      final state = GameState(
        rack: [regularTile(TileColor.red, 5)],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.blue, 9),
              regularTile(TileColor.black, 9),
              regularTile(TileColor.orange, 9),
            ],
          ),
        ],
      );

      final moves = useCase(state, isFirstMeldTurn: true).moves;

      expect(moves, isEmpty);
    });

    test('givenFirstMeldAbove30_whenSolved_thenAllowsMove', () {
      final state = GameState(
        rack: [
          regularTile(TileColor.red, 10),
          regularTile(TileColor.red, 11),
          regularTile(TileColor.red, 12),
        ],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.blue, 9),
              regularTile(TileColor.black, 9),
              regularTile(TileColor.orange, 9),
            ],
          ),
        ],
      );

      final moves = useCase(state, isFirstMeldTurn: true).moves;

      expect(moves, isNotEmpty);
      final maxPlayed =
          moves.map((m) => m.tilesPlayedFromRack).reduce((a, b) => a > b ? a : b);
      expect(maxPlayed, 3);
      for (final move in moves) {
        expect(move.tilesPlayedFromRack, maxPlayed);
        final rackPlayed = [
          for (final meld in move.finalTableMelds)
            ...meld.tiles.where(
              (t) => state.rack.any((r) => r.id == t.id),
            ),
        ];
        expect(
          RulesValidator.satisfiesFirstMeldPlay(rackPlayed),
          isTrue,
        );
        expect(
          RulesValidator.scoreTilesFromRack(rackPlayed),
          greaterThanOrEqualTo(RulesConstants.initialMeldMinimumPoints),
        );
      }
    });

    test('givenMultipleOptimal_whenSolved_thenAllHaveSameMax', () {
      final state = GameState(
        rack: [regularTile(TileColor.orange, 8)],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.red, 8),
              regularTile(TileColor.blue, 8),
              regularTile(TileColor.black, 8),
            ],
          ),
        ],
      );

      final moves = useCase(state, isFirstMeldTurn: false).moves;
      final max =
          moves.map((m) => m.tilesPlayedFromRack).reduce((a, b) => a > b ? a : b);

      expect(moves.every((m) => m.tilesPlayedFromRack == max), isTrue);
    });

    test('givenEmptyRack_whenSolved_thenZeroTilesPlayed', () {
      final state = GameState(
        rack: const [],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.red, 4),
              regularTile(TileColor.blue, 4),
              regularTile(TileColor.black, 4),
            ],
          ),
        ],
      );

      final moves = MoveSolver.findOptimalMoves(
        state,
        isFirstMeldTurn: false,
      ).moves;

      expect(moves, isNotEmpty);
      expect(moves.first.tilesPlayedFromRack, 0);
    });
  });
}
