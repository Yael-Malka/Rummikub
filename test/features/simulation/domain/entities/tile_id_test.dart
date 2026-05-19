import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_id.dart';

void main() {
  group('TileId', () {
    test('givenSameRegularId_whenCompared_thenEqual', () {
      const a = RegularTileId(
        color: TileColor.red,
        number: 7,
        copyIndex: 1,
      );
      const b = RegularTileId(
        color: TileColor.red,
        number: 7,
        copyIndex: 1,
      );
      const c = RegularTileId(
        color: TileColor.red,
        number: 7,
        copyIndex: 0,
      );

      expect(a, b);
      expect(a == c, isFalse);
    });

    test('givenJokerIds_whenDifferentCopy_thenNotEqual', () {
      const j0 = JokerTileId(copyIndex: 0);
      const j1 = JokerTileId(copyIndex: 1);

      expect(j0 == j1, isFalse);
    });
  });
}
