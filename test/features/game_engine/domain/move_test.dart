import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/entities/move.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('Move equality', () {
    test(
      'givenSameMeldsDifferentDeckCopy_whenCompared_thenEqual',
      () {
        final t3a = regularTile(TileColor.red, 3, copyIndex: 0);
        final t4a = regularTile(TileColor.red, 4, copyIndex: 0);
        final t5a = regularTile(TileColor.red, 5, copyIndex: 0);

        final t3b = regularTile(TileColor.red, 3, copyIndex: 1);
        final t4b = regularTile(TileColor.red, 4, copyIndex: 1);
        final t5b = regularTile(TileColor.red, 5, copyIndex: 1);

        final moveA = Move(
          tilesPlayedFromRack: 3,
          finalTableMelds: [
            Meld(type: MeldType.run, tiles: [t3a, t4a, t5a]),
          ],
          finalRack: const [],
        );

        final moveB = Move(
          tilesPlayedFromRack: 3,
          finalTableMelds: [
            Meld(type: MeldType.run, tiles: [t3b, t4b, t5b]),
          ],
          finalRack: const [],
        );

        expect(moveA, equals(moveB));
        expect(moveA.tableLayoutKey, moveB.tableLayoutKey);
        expect(moveA.visibleOutcomeKey, moveB.visibleOutcomeKey);
      },
    );

    test(
      'givenSameMeldsDifferentTileOrder_whenCompared_thenEqual',
      () {
        final t3 = regularTile(TileColor.red, 3);
        final t4 = regularTile(TileColor.red, 4);
        final t5 = regularTile(TileColor.red, 5);

        final moveA = Move(
          tilesPlayedFromRack: 3,
          finalTableMelds: [
            Meld(type: MeldType.run, tiles: [t3, t4, t5]),
          ],
          finalRack: const [],
        );

        final moveB = Move(
          tilesPlayedFromRack: 3,
          finalTableMelds: [
            Meld(type: MeldType.run, tiles: [t5, t3, t4]),
          ],
          finalRack: const [],
        );

        expect(moveA, equals(moveB));
        expect(moveA.canonicalKey, moveB.canonicalKey);
      },
    );

    test(
      'givenDifferentMeldPartitions_whenCompared_thenNotEqual',
      () {
        final moveA = Move(
          tilesPlayedFromRack: 2,
          finalTableMelds: [
            Meld(
              type: MeldType.run,
              tiles: [
                regularTile(TileColor.orange, 2),
                regularTile(TileColor.orange, 3),
                regularTile(TileColor.orange, 4),
              ],
            ),
            Meld(
              type: MeldType.run,
              tiles: [
                regularTile(TileColor.orange, 5),
                regularTile(TileColor.orange, 6),
                regularTile(TileColor.orange, 7),
              ],
            ),
          ],
          finalRack: const [],
        );

        final moveB = Move(
          tilesPlayedFromRack: 2,
          finalTableMelds: [
            Meld(
              type: MeldType.run,
              tiles: [
                regularTile(TileColor.orange, 2),
                regularTile(TileColor.orange, 3),
                regularTile(TileColor.orange, 4),
                regularTile(TileColor.orange, 5),
                regularTile(TileColor.orange, 6),
                regularTile(TileColor.orange, 7),
              ],
            ),
          ],
          finalRack: const [],
        );

        expect(moveA, isNot(equals(moveB)));
        expect(moveA.canonicalKey, isNot(moveB.canonicalKey));
      },
    );
  });
}
