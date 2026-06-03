import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/joker_role_inferrer.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import 'test_tiles.dart';

void main() {
  group('JokerRoleInferrer', () {
    test('givenJokerInRun_whenInfer_thenFillsGap', () {
      final meld = Meld(
        type: MeldType.run,
        tiles: [
          regularTile(TileColor.red, 5),
          jokerTile(copyIndex: 0),
          regularTile(TileColor.red, 7),
        ],
      );

      final roles = JokerRoleInferrer.forMeld(meld);

      expect(roles, hasLength(1));
      expect(roles.single.standsInForNumber, 6);
      expect(roles.single.standsInForColor, TileColor.red);
    });
  });
}
