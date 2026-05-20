import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move_step.dart';
import 'package:rummikub_app/features/game_engine/domain/move_steps_builder.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('MoveStepsBuilder', () {
    test('givenTilesPlayed_whenBuild_thenIncludesPlayStep', () {
      final before = GameState(
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
      final move = Move(
        tilesPlayedFromRack: 1,
        finalRack: const [],
        finalTableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              regularTile(TileColor.red, 8),
              regularTile(TileColor.blue, 8),
              regularTile(TileColor.black, 8),
              regularTile(TileColor.orange, 8),
            ],
          ),
        ],
      );

      final steps = MoveStepsBuilder.buildSteps(
        stateBefore: before,
        move: move,
      );

      expect(steps.whereType<PlayTilesFromRackStep>(), hasLength(1));
      final playStep = steps.whereType<PlayTilesFromRackStep>().first;
      expect(playStep.tiles, hasLength(1));
      expect(playStep.tiles.first.number, 8);
    });

    test('givenTableReorganized_whenBuild_thenIncludesReorganizeStep', () {
      final before = GameState(
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
      final move = Move(
        tilesPlayedFromRack: 2,
        finalRack: const [],
        finalTableMelds: [
          Meld(
            type: MeldType.run,
            tiles: [
              regularTile(TileColor.orange, 5),
              regularTile(TileColor.orange, 6),
              regularTile(TileColor.orange, 7),
              regularTile(TileColor.orange, 8),
              regularTile(TileColor.orange, 9),
            ],
          ),
        ],
      );

      final steps = MoveStepsBuilder.buildSteps(
        stateBefore: before,
        move: move,
      );

      expect(steps.whereType<ReorganizeTableStep>(), isNotEmpty);
    });
  });
}
