import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/data/models/game_state_codec.dart';
import 'package:rummikub_app/features/simulation/data/models/saved_session.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';

import '../../../game_engine/domain/test_tiles.dart';

void main() {
  group('GameStateCodec', () {
    test('givenSession_whenRoundTrip_thenEquals', () {
      final session = SavedSession(
        isFirstMeldTurn: true,
        gameState: GameState(
          rack: [regularTile(TileColor.red, 3), jokerTile()],
          tableMelds: [
            Meld(
              type: MeldType.group,
              tiles: [
                regularTile(TileColor.blue, 9),
                regularTile(TileColor.black, 9),
                regularTile(TileColor.orange, 9),
              ],
            ),
          ],
        ),
      );

      final encoded = GameStateCodec.encodeSession(session);
      final decoded = GameStateCodec.decodeSession(encoded);

      expect(decoded, isNotNull);
      expect(decoded!.isFirstMeldTurn, isTrue);
      expect(
        decoded.gameState.usedTileIds,
        session.gameState.usedTileIds,
      );
    });
  });
}
