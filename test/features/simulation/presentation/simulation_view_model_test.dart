import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/repositories/game_state_repository.dart';
import 'package:rummikub_app/features/simulation/domain/usecases/generate_simulated_state_use_case.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/state/simulation_state.dart';

import '../../game_engine/domain/test_tiles.dart';

final class _FakeGameStateRepository implements GameStateRepository {
  _FakeGameStateRepository(this._state, {this.shouldThrow = false});

  final GameState _state;
  final bool shouldThrow;

  @override
  GameState generateSimulatedState() {
    if (shouldThrow) {
      throw Exception('repository failure');
    }
    return _state;
  }
}

GameState _validGameState() {
  return GameState(
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
}

void main() {
  group('SimulationViewModel', () {
    test('givenNewInstance_whenCreated_thenStateIsInitial', () {
      final viewModel = SimulationViewModel(
        GenerateSimulatedStateUseCase(
          _FakeGameStateRepository(_validGameState()),
        ),
      );

      expect(viewModel.state, isA<SimulationInitial>());
    });

    test('givenSuccess_whenSimulate_thenStateIsLoaded', () async {
      final expected = _validGameState();
      final viewModel = SimulationViewModel(
        GenerateSimulatedStateUseCase(
          _FakeGameStateRepository(expected),
        ),
      );

      await viewModel.simulate();

      expect(viewModel.state, isA<SimulationLoaded>());
      final loaded = viewModel.state as SimulationLoaded;
      expect(loaded.gameState, expected);
    });

    test('givenFailure_whenSimulate_thenStateIsError', () async {
      final viewModel = SimulationViewModel(
        GenerateSimulatedStateUseCase(
          _FakeGameStateRepository(
            _validGameState(),
            shouldThrow: true,
          ),
        ),
      );

      await viewModel.simulate();

      expect(viewModel.state, isA<SimulationError>());
    });
  });
}
