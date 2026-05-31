import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/core/constants/rules_constants.dart';
import 'package:rummikub_app/features/game_engine/domain/rules_validator.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move.dart';
import 'package:rummikub_app/features/game_engine/domain/set_cover_move_solver.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  int maxTilesPlayed(List<Move> moves) {
    return moves
        .map((m) => m.tilesPlayedFromRack)
        .reduce((a, b) => a > b ? a : b);
  }

  void expectEveryFirstMeldMoveValid(List<Move> moves) {
    for (final move in moves) {
      expect(move.tilesPlayedFromRack, greaterThan(0));
      final played = move.finalTableMelds.expand((m) => m.tiles);
      expect(
        RulesValidator.satisfiesFirstMeldPlay(played),
        isTrue,
        reason: 'move must score 30+ from rack tiles played',
      );
    }
  }

  group('SetCoverMoveSolver — table with melds', () {
    test('givenTableRunAndRackExtension_whenSolved_thenPlaysRackTile', () {
      final state = GameState(
        rack: [regularTile(TileColor.red, 6)],
        tableMelds: [
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.red, 3),
              regularTile(TileColor.red, 4),
              regularTile(TileColor.red, 5),
            ],
          ),
        ],
      );

      final moves =
          SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: false);

      expect(moves, isNotEmpty);
      expect(maxTilesPlayed(moves), 1);
    });

    test('givenReorganizeOrGroup_whenSolved_thenMaximizesRack', () {
      final state = GameState(
        rack: [
          regularTile(TileColor.red, 6),
          regularTile(TileColor.blue, 5),
          regularTile(TileColor.black, 5),
        ],
        tableMelds: [
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.red, 3),
              regularTile(TileColor.red, 4),
              regularTile(TileColor.red, 5),
            ],
          ),
        ],
      );

      final moves =
          SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: false);

      expect(maxTilesPlayed(moves), 1);
    });
  });

  group('SetCoverMoveSolver — empty table (opening)', () {
    test('givenEmptyTableAndEmptyRack_whenSolved_thenNoMoves', () {
      const state = GameState(rack: [], tableMelds: []);

      final moves =
          SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: false);

      expect(moves, isEmpty);
    });

    test(
      'givenEmptyTableFullRackRun_whenFirstMeld_thenPlaysAllAndClearsRack',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 10),
            regularTile(TileColor.red, 11),
            regularTile(TileColor.red, 12),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: true);

        expect(moves, isNotEmpty);
        expect(maxTilesPlayed(moves), 3);
        expectEveryFirstMeldMoveValid(moves);
        for (final move in moves) {
          expect(move.finalRack, isEmpty);
          expect(move.finalTableMelds.length, 1);
        }
      },
    );

    test(
      'givenFirstMeld_whenMoreTilesStillMeet30_thenMaximizesTileCount',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 10),
            regularTile(TileColor.red, 11),
            regularTile(TileColor.red, 12),
            regularTile(TileColor.red, 13),
            regularTile(TileColor.blue, 1),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: true);

        expect(moves, isNotEmpty);
        expect(maxTilesPlayed(moves), 4);
        expectEveryFirstMeldMoveValid(moves);
        expect(
          moves.every((m) => m.finalRack.length == 1),
          isTrue,
        );
      },
    );

    test(
      'givenFirstMeld_whenOnlySmallMeldMeets30_thenDoesNotPreferInvalidHighCount',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 10),
            regularTile(TileColor.red, 11),
            regularTile(TileColor.red, 12),
            regularTile(TileColor.blue, 1),
            regularTile(TileColor.black, 2),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: true);

        expect(moves, isNotEmpty);
        expect(maxTilesPlayed(moves), 3);
        expectEveryFirstMeldMoveValid(moves);
      },
    );

    test(
      'givenEmptyTableOrphanTile_whenFirstMeld_thenPlaysMaxLegalAndLeavesRest',
      () {
        final orphan = regularTile(TileColor.red, 2);
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 10),
            regularTile(TileColor.red, 11),
            regularTile(TileColor.red, 12),
            orphan,
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: true);

        expect(moves, isNotEmpty);
        expect(maxTilesPlayed(moves), 3);
        for (final move in moves) {
          expect(move.finalRack.length, 1);
          expect(move.finalRack.first.id, orphan.id);
          expect(move.tilesPlayedFromRack, 3);
        }
      },
    );

    test(
      'givenEmptyTableBelow30_whenFirstMeld_thenNoMoves',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 3),
            regularTile(TileColor.red, 4),
            regularTile(TileColor.red, 5),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: true);

        expect(moves, isEmpty);
      },
    );

    test(
      'givenEmptyTableFullRackRun_whenNotFirstMeld_thenPlaysAllWithout30Check',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.blue, 1),
            regularTile(TileColor.blue, 2),
            regularTile(TileColor.blue, 3),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: false);

        expect(moves, isNotEmpty);
        expect(maxTilesPlayed(moves), 3);
        for (final move in moves) {
          expect(move.finalRack, isEmpty);
        }
      },
    );

    test(
      'givenEmptyTableMultipleOptimal_whenSolved_thenAllShareSameMax',
      () {
        final state = GameState(
          rack: [
            regularTile(TileColor.red, 8),
            regularTile(TileColor.blue, 8),
            regularTile(TileColor.black, 8),
            regularTile(TileColor.orange, 8),
          ],
          tableMelds: const [],
        );

        final moves =
            SetCoverMoveSolver.findOptimalMoves(state, isFirstMeldTurn: false);

        expect(moves, isNotEmpty);
        final max = maxTilesPlayed(moves);
        expect(moves.every((m) => m.tilesPlayedFromRack == max), isTrue);
        expect(max, 4);
      },
    );
  });
}
