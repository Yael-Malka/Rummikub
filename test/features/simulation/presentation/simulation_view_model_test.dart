import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/repositories/game_state_repository.dart';
import 'package:rummikub_app/features/simulation/domain/usecases/generate_simulated_state_use_case.dart';
import 'package:rummikub_app/core/services/session_storage.dart';
import 'package:rummikub_app/features/simulation/data/models/saved_session.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/state/optimal_moves_state.dart';
import 'package:rummikub_app/features/simulation/presentation/state/simulation_state.dart';

import '../../game_engine/domain/test_tiles.dart';

final class _FakeGameStateRepository implements GameStateRepository {
  _FakeGameStateRepository(this._state, {this.shouldThrow = false});

  final GameState _state;
  final bool shouldThrow;

  var lastEmptyTable = false;

  @override
  GameState generateSimulatedState({bool emptyTable = false}) {
    lastEmptyTable = emptyTable;
    if (shouldThrow) {
      throw Exception('repository failure');
    }
    return _state;
  }
}

GameState _validGameState() {
  return GameState(
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
}

final class _FakeSessionStorage implements SessionStorage {
  SavedSession? saved;

  @override
  Future<void> clearLastSession() async {
    saved = null;
  }

  @override
  Future<SavedSession?> loadLastSession() async => saved;

  @override
  Future<void> saveLastSession(SavedSession session) async {
    saved = session;
  }
}

SimulationViewModel _viewModel(
  GameState state, {
  _FakeSessionStorage? sessionStorage,
}) {
  return SimulationViewModel(
    GenerateSimulatedStateUseCase(_FakeGameStateRepository(state)),
    sessionStorage: sessionStorage ?? _FakeSessionStorage(),
  );
}

void main() {
  group('SimulationViewModel', () {
    test('givenNewInstance_whenCreated_thenStateIsInitial', () {
      final viewModel = _viewModel(_validGameState());

      expect(viewModel.state, isA<SimulationInitial>());
      expect(viewModel.optimalMovesState, isA<OptimalMovesIdle>());
    });

    test('givenSuccess_whenSimulate_thenStateIsLoaded', () async {
      final expected = _validGameState();
      final viewModel = _viewModel(expected);

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

    test('givenLoaded_whenFindOptimalMoves_thenMovesLoaded', () async {
      final viewModel = _viewModel(_validGameState());

      await viewModel.simulate();
      await viewModel.findOptimalMoves();

      expect(viewModel.optimalMovesState, isA<OptimalMovesLoaded>());
      final loaded = viewModel.optimalMovesState as OptimalMovesLoaded;
      expect(loaded.moves, isNotEmpty);
      expect(
        loaded.moves.any((move) => move.tilesPlayedFromRack > 0),
        isTrue,
      );
    });

    test('givenFirstMeldToggle_whenChanged_thenUpdatesFlag', () async {
      final viewModel = _viewModel(_validGameState());

      viewModel.setFirstMeldTurn(true);

      expect(viewModel.isFirstMeldTurn, isTrue);
    });

    test('givenEmptyTableToggle_whenSimulate_thenPassesFlagToGenerator', () async {
      final repo = _FakeGameStateRepository(_validGameState());
      final viewModel = SimulationViewModel(
        GenerateSimulatedStateUseCase(repo),
      );

      viewModel.setEmptyTable(true);
      await viewModel.simulate();

      expect(repo.lastEmptyTable, isTrue);
      expect(viewModel.emptyTable, isTrue);
    });

    test('givenNewSimulation_whenSimulate_thenResetsFirstMeldToggle', () async {
      final viewModel = _viewModel(_validGameState());

      await viewModel.simulate();
      viewModel.setFirstMeldTurn(true);
      await viewModel.simulate();

      expect(viewModel.isFirstMeldTurn, isFalse);
      expect(viewModel.optimalMovesState, isA<OptimalMovesIdle>());
    });

    test('givenSavedSession_whenRestored_thenStateIsLoaded', () async {
      final storage = _FakeSessionStorage();
      final saved = SavedSession(
        gameState: _validGameState(),
        isFirstMeldTurn: true,
      );
      storage.saved = saved;

      final viewModel = _viewModel(_validGameState(), sessionStorage: storage);
      await Future<void>.delayed(Duration.zero);

      expect(viewModel.state, isA<SimulationLoaded>());
      expect(viewModel.isFirstMeldTurn, isTrue);
      expect(viewModel.wasSessionRestored, isTrue);
    });

    test('givenSimulateSuccess_whenSaved_thenPersistsSession', () async {
      final storage = _FakeSessionStorage();
      final viewModel = _viewModel(_validGameState(), sessionStorage: storage);

      await viewModel.simulate();
      await Future<void>.delayed(Duration.zero);

      expect(storage.saved, isNotNull);
      expect(
        storage.saved!.gameState.usedTileIds,
        _validGameState().usedTileIds,
      );
    });
  });
}
