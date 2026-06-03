import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/move_solver.dart';
import 'package:rummikub_app/features/game_engine/domain/table_extension_solver.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('TableExtensionSolver', () {
    test('givenRedRunOnTable_whenExtendWith45_thenValidLayout', () {
      final tableMelds = [
        Meld(
          type: MeldType.run,
          tiles: [
            regularTile(TileColor.red, 10),
            regularTile(TileColor.red, 9),
            regularTile(TileColor.red, 8),
            regularTile(TileColor.red, 7),
            regularTile(TileColor.red, 6),
          ],
        ),
      ];
      final played = [
        regularTile(TileColor.red, 4),
        regularTile(TileColor.red, 5),
      ];

      final layouts = TableExtensionSolver.findExtendedLayouts(
        tableMelds,
        played,
      );

      expect(layouts, isNotEmpty);
      final extended = layouts.first.first;
      expect(extended.tiles.length, 7);
      expect(
        extended.tiles.map((t) => t.number).toSet(),
        {4, 5, 6, 7, 8, 9, 10},
      );
    });
  });

  group('MoveSolver — large table', () {
    test('givenRed45AndBigTable_whenSolved_thenPlaysTwoTiles', () {
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

      final moves =
          MoveSolver.findOptimalMoves(state, isFirstMeldTurn: false).moves;
      final maxPlayed =
          moves.map((m) => m.tilesPlayedFromRack).fold(0, (a, b) => a > b ? a : b);

      expect(maxPlayed, greaterThanOrEqualTo(2));
    });
  });
}
