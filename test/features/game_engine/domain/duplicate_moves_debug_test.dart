import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/set_cover_move_solver.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  test('duplicate red-6 copies extending run yields one visible move', () {
    final state = GameState(
      rack: [
        regularTile(TileColor.red, 6),
        regularTile(TileColor.red, 6, copyIndex: 1),
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

    final moves = SetCoverMoveSolver.findOptimalMoves(
      state,
      isFirstMeldTurn: false,
    ).moves;

    expect(
      moves.map((m) => m.tilesPlayedFromRack).fold(0, (a, b) => a > b ? a : b),
      1,
    );
    expect(moves.map((m) => m.visibleOutcomeKey).toSet().length, 1);
  });

  test(
    'givenDuplicateRackTilesAndTableReorg_whenSolved_thenOneVisibleOutcome',
    () {
      final state = GameState(
        rack: [
          regularTile(TileColor.red, 4),
          regularTile(TileColor.red, 5, copyIndex: 1),
          regularTile(TileColor.black, 1),
        ],
        tableMelds: [
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.black, 11),
              regularTile(TileColor.black, 10),
              regularTile(TileColor.black, 9),
            ],
          ),
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.orange, 13),
              regularTile(TileColor.orange, 12),
              regularTile(TileColor.orange, 11),
              regularTile(TileColor.orange, 10),
              regularTile(TileColor.orange, 9),
            ],
          ),
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.black, 7),
              regularTile(TileColor.blue, 7),
              regularTile(TileColor.red, 7, copyIndex: 1),
              regularTile(TileColor.orange, 7),
            ],
          ),
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.red, 10),
              regularTile(TileColor.red, 9),
              regularTile(TileColor.red, 8),
              regularTile(TileColor.red, 7, copyIndex: 0),
              regularTile(TileColor.red, 6),
            ],
          ),
        ],
      );

      final moves = SetCoverMoveSolver.findOptimalMoves(
        state,
        isFirstMeldTurn: false,
      ).moves;

      expect(
        moves.map((m) => m.tilesPlayedFromRack).fold(0, (a, b) => a > b ? a : b),
        2,
      );
      expect(moves.map((m) => m.visibleOutcomeKey).toSet().length, 1);
    },
  );
}
