import 'package:flutter/foundation.dart';

import '../../../game_engine/domain/usecases/find_optimal_moves_use_case.dart';
import '../../domain/exceptions/state_generation_exception.dart';
import '../../domain/usecases/generate_simulated_state_use_case.dart';
import '../state/optimal_moves_state.dart';
import '../state/simulation_state.dart';

/// ViewModel for simulation flow.
class SimulationViewModel extends ChangeNotifier {
  SimulationViewModel(
    this._generateSimulatedState,
    this._findOptimalMoves,
  );

  final GenerateSimulatedStateUseCase _generateSimulatedState;
  final FindOptimalMovesUseCase _findOptimalMoves;

  SimulationState _state = const SimulationInitial();
  OptimalMovesState _optimalMovesState = const OptimalMovesIdle();
  bool _isFirstMeldTurn = false;

  SimulationState get state => _state;

  OptimalMovesState get optimalMovesState => _optimalMovesState;

  bool get isFirstMeldTurn => _isFirstMeldTurn;

  void setFirstMeldTurn(bool value) {
    if (_isFirstMeldTurn == value) {
      return;
    }
    _isFirstMeldTurn = value;
    _resetOptimalMoves();
    notifyListeners();
  }

  Future<void> simulate() async {
    _resetOptimalMoves();
    _isFirstMeldTurn = false;
    _setState(const SimulationLoading());

    try {
      final gameState = _generateSimulatedState();
      _setState(SimulationLoaded(gameState));
    } on StateGenerationException catch (error) {
      _setState(SimulationError(error.message));
    } catch (error) {
      _setState(SimulationError(error.toString()));
    }
  }

  Future<void> findOptimalMoves() async {
    final current = _state;
    if (current is! SimulationLoaded) {
      return;
    }

    _setOptimalMovesState(const OptimalMovesLoading());
    await Future<void>.delayed(Duration.zero);

    try {
      final moves = _findOptimalMoves(
        current.gameState,
        isFirstMeldTurn: _isFirstMeldTurn,
      );
      _setOptimalMovesState(OptimalMovesLoaded(moves));
    } catch (error) {
      _setOptimalMovesState(OptimalMovesError(error.toString()));
    }
  }

  void _resetOptimalMoves() {
    _optimalMovesState = const OptimalMovesIdle();
  }

  void _setState(SimulationState newState) {
    _state = newState;
    notifyListeners();
  }

  void _setOptimalMovesState(OptimalMovesState newState) {
    _optimalMovesState = newState;
    notifyListeners();
  }
}
