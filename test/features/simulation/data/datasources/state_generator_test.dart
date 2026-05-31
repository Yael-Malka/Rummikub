import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/core/constants/simulation_constants.dart';
import 'package:rummikub_app/features/game_engine/domain/full_deck.dart';
import 'package:rummikub_app/features/game_engine/domain/rules_validator.dart';
import 'package:rummikub_app/features/simulation/data/datasources/state_generator.dart';

void main() {
  group('StateGenerator', () {
    test('givenSeededRandom_whenGenerate_thenStateIsValid', () {
      final generator = StateGenerator(random: Random(42));
      final state = generator.generate();

      expect(RulesValidator.validateGameState(state).isValid, isTrue);
      expect(FullDeck.hasUniqueIds(state.allTiles), isTrue);
    });

    test('givenGenerate_whenRackSize_thenWithinBounds', () {
      final generator = StateGenerator(random: Random(7));
      final state = generator.generate();

      expect(state.rackSize, greaterThanOrEqualTo(SimulationConstants.minRackSize));
      expect(state.rackSize, lessThanOrEqualTo(SimulationConstants.maxRackSize));
    });

    test('givenGenerate_whenTableMelds_thenEachMeldIsValid', () {
      final generator = StateGenerator(random: Random(99));
      final state = generator.generate();

      expect(state.tableMelds, isNotEmpty);
      for (final meld in state.tableMelds) {
        expect(RulesValidator.validateMeld(meld).isValid, isTrue);
      }
    });

    test('givenManyGenerations_whenRun_thenNoDuplicateTileIds', () {
      final generator = StateGenerator(random: Random(1234));

      for (var i = 0; i < 100; i++) {
        final state = generator.generate();
        expect(FullDeck.hasUniqueIds(state.allTiles), isTrue,
            reason: 'generation $i');
      }
    });

    test('givenGenerate_whenTileCount_thenSubsetOfDeck', () {
      final generator = StateGenerator(random: Random(5));
      final state = generator.generate();

      expect(state.allTiles.length, lessThanOrEqualTo(FullDeck.tileCount));
    });

    test('givenEmptyTableFlag_whenGenerate_thenTableHasNoMelds', () {
      final generator = StateGenerator(random: Random(42));
      final state = generator.generate(emptyTable: true);

      expect(RulesValidator.validateGameState(state).isValid, isTrue);
      expect(state.tableMelds, isEmpty);
      expect(state.rackSize, greaterThanOrEqualTo(SimulationConstants.minRackSize));
    });
  });
}
