import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_id.dart';

void main() {
  group('GameState', () {
    const tileA = Tile(
      id: RegularTileId(color: TileColor.red, number: 5, copyIndex: 0),
    );
    const tileB = Tile(
      id: RegularTileId(color: TileColor.blue, number: 5, copyIndex: 0),
    );
    const tileC = Tile(
      id: RegularTileId(color: TileColor.black, number: 5, copyIndex: 0),
    );

    test('givenRackAndTable_whenAllTiles_thenCountsAreCorrect', () {
      final state = GameState(
        rack: [tileA],
        tableMelds: [
          Meld(type: MeldType.group, tiles: [tileB, tileC, tileA]),
        ],
      );

      expect(state.allTiles.length, 4);
      expect(state.usedTileIds.length, 3);
      expect(state.rackSize, 1);
      expect(state.tableTileCount, 3);
    });

    test('givenRackOnly_whenUsedTileIds_thenMatchesRack', () {
      const state = GameState(rack: [tileA, tileB], tableMelds: []);

      expect(state.usedTileIds, {tileA.id, tileB.id});
    });
  });
}
