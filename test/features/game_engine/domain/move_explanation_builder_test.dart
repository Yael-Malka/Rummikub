import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move_explanation.dart';
import 'package:rummikub_app/features/game_engine/domain/move_explanation_builder.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('MoveExplanationBuilder', () {
    test('givenGroupExtension_whenBuild_thenExtendStepOnly', () {
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

      final explanation = MoveExplanationBuilder.build(
        stateBefore: before,
        move: move,
      );

      expect(explanation.steps, hasLength(1));
      expect(explanation.steps.single, isA<ExtendMeldStep>());
      expect(explanation.summary.isTableValid, isTrue);
      expect(explanation.summary.tilesPlayedFromRack, 1);
      expect(explanation.highlightedRackTileIds, hasLength(1));
    });

    test('givenRunExtension_whenBuild_thenExtendNotReorganize', () {
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

      final explanation = MoveExplanationBuilder.build(
        stateBefore: before,
        move: move,
      );

      expect(explanation.steps.whereType<ExtendMeldStep>(), hasLength(1));
      expect(explanation.steps.whereType<BreakMeldStep>(), isEmpty);
      expect(explanation.steps.whereType<BuildMeldStep>(), isEmpty);
    });

    test('givenSummary_whenBuild_thenReportsValidityAndRackLeft', () {
      final before = GameState(
        rack: [
          regularTile(TileColor.orange, 8),
          regularTile(TileColor.orange, 9),
        ],
        tableMelds: const [],
      );
      final move = Move(
        tilesPlayedFromRack: 0,
        finalRack: before.rack,
        finalTableMelds: const [],
      );

      final explanation = MoveExplanationBuilder.build(
        stateBefore: before,
        move: move,
      );

      expect(explanation.summary.tilesPlayedFromRack, 0);
      expect(explanation.summary.rackTilesRemaining, 2);
      expect(explanation.summary.isTableValid, isTrue);
    });
  });
}
