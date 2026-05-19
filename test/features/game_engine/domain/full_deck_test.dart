import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/core/constants/deck_constants.dart';
import 'package:rummikub_app/features/game_engine/domain/full_deck.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_id.dart';

void main() {
  group('FullDeck', () {
    late List<Tile> deck;

    setUp(() {
      deck = FullDeck.create();
    });

    test('givenCreate_whenCalled_thenReturns106Tiles', () {
      expect(deck.length, DeckConstants.tileCount);
    });

    test('givenCreate_whenCalled_thenAllTileIdsAreUnique', () {
      expect(FullDeck.hasUniqueIds(deck), isTrue);
    });

    test('givenCreate_whenCounted_thenTwoCopiesPerColorAndNumber', () {
      for (final color in [
        TileColor.red,
        TileColor.blue,
        TileColor.black,
        TileColor.orange,
      ]) {
        for (var n = 1; n <= 13; n++) {
          expect(
            FullDeck.countRegular(deck, color: color, number: n),
            DeckConstants.copiesPerNumber,
          );
        }
      }
    });

    test('givenCreate_whenCounted_thenExactlyTwoJokers', () {
      final jokers = deck.where((t) => t.id is JokerTileId).toList();
      expect(jokers.length, DeckConstants.jokerCount);
      expect(jokers.map((t) => t.id).toSet().length, 2);
    });

    test('givenCreate_whenSummed_then104NumberedPlus2Jokers', () {
      final numbered =
          deck.where((t) => t.id is RegularTileId).length;
      final jokers = deck.where((t) => t.id is JokerTileId).length;

      expect(numbered, 104);
      expect(jokers, 2);
      expect(numbered + jokers, 106);
    });

    test('givenDuplicateIdInList_whenHasUniqueIds_thenReturnsFalse', () {
      final first = deck.first;
      final duplicate = [
        first,
        Tile(id: first.id),
      ];
      expect(FullDeck.hasUniqueIds(duplicate), isFalse);
    });
  });
}
