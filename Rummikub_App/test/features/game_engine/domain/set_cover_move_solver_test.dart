import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/set_cover_move_solver.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('SetCoverMoveSolver', () {
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
      final maxPlayed = moves
          .map((m) => m.tilesPlayedFromRack)
          .reduce((a, b) => a > b ? a : b);
      expect(maxPlayed, 1);
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

      final maxPlayed = moves
          .map((m) => m.tilesPlayedFromRack)
          .reduce((a, b) => a > b ? a : b);
      // Best legal move extends the run (1 tile), not the 5-5-5 group alone.
      expect(maxPlayed, 1);
    });
  });
}
