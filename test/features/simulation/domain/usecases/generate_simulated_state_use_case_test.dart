import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/game_engine/domain/rules_validator.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/exceptions/state_generation_exception.dart';
import 'package:rummikub_app/features/simulation/domain/repositories/game_state_repository.dart';
import 'package:rummikub_app/features/simulation/domain/usecases/generate_simulated_state_use_case.dart';

import '../../../game_engine/domain/test_tiles.dart';

final class _FakeGameStateRepository implements GameStateRepository {
  _FakeGameStateRepository(this._state);

  final GameState _state;

  @override
  GameState generateSimulatedState({bool emptyTable = false}) => _state;
}

void main() {
  group('GenerateSimulatedStateUseCase', () {
    test('givenValidRepository_whenCall_thenReturnsState', () {
      final validState = GameState(
        rack: [regularTile(TileColor.orange, 2)],
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

      final useCase = GenerateSimulatedStateUseCase(
        _FakeGameStateRepository(validState),
      );

      final result = useCase();

      expect(result, validState);
      expect(RulesValidator.validateGameState(result).isValid, isTrue);
    });

    test('givenInvalidRepository_whenCall_thenThrows', () {
      final duplicate = regularTile(TileColor.red, 5);
      final invalidState = GameState(
        rack: [duplicate],
        tableMelds: [
          Meld(
            type: MeldType.group,
            tiles: [
              duplicate,
              regularTile(TileColor.blue, 5),
              regularTile(TileColor.black, 5),
            ],
          ),
        ],
      );

      final useCase = GenerateSimulatedStateUseCase(
        _FakeGameStateRepository(invalidState),
      );

      expect(() => useCase(), throwsA(isA<StateGenerationException>()));
    });
  });
}
