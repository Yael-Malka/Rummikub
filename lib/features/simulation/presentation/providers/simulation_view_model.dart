import 'package:flutter/foundation.dart';

import '../../../../core/services/session_storage.dart';
import '../../../../core/services/solver_logger.dart';
import '../../domain/services/optimal_moves_computer.dart';
import '../../data/models/saved_session.dart';
import '../../domain/exceptions/state_generation_exception.dart';
import '../../domain/usecases/generate_simulated_state_use_case.dart';
import '../state/optimal_moves_state.dart';
import '../state/simulation_state.dart';

/// ViewModel for simulation flow.
class SimulationViewModel extends ChangeNotifier {
  SimulationViewModel(
    this._generateSimulatedState, {
    SessionStorage? sessionStorage,
  }) : _sessionStorage = sessionStorage ?? const NoOpSessionStorage() {
    _restoreLastSession();
  }

  final GenerateSimulatedStateUseCase _generateSimulatedState;
  final SessionStorage _sessionStorage;

  SimulationState _state = const SimulationInitial();
  OptimalMovesState _optimalMovesState = const OptimalMovesIdle();
  bool _isFirstMeldTurn = false;
  bool _emptyTable = false;
  bool _wasSessionRestored = false;

  SimulationState get state => _state;

  OptimalMovesState get optimalMovesState => _optimalMovesState;

  bool get isFirstMeldTurn => _isFirstMeldTurn;

  bool get emptyTable => _emptyTable;

  bool get wasSessionRestored => _wasSessionRestored;

  void setEmptyTable(bool value) {
    if (_emptyTable == value) {
      return;
    }
    _emptyTable = value;
    if (value) {
      _isFirstMeldTurn = true;
    }
    _resetOptimalMoves();
    notifyListeners();
  }

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
    _wasSessionRestored = false;
    if (!_emptyTable) {
      _isFirstMeldTurn = false;
    }
    _setState(const SimulationLoading());

    try {
      final gameState = _generateSimulatedState(emptyTable: _emptyTable);
      _setState(SimulationLoaded(gameState));
      await _sessionStorage.saveLastSession(
        SavedSession(
          gameState: gameState,
          isFirstMeldTurn: _isFirstMeldTurn,
          emptyTable: _emptyTable,
        ),
      );
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
    SolverLogger.info('UI: optimal-move search requested');
    // Brief delay so loading UI paints before isolate work starts.
    await Future<void>.delayed(const Duration(milliseconds: 50));

    try {
      final moves = await OptimalMovesComputer.run(
        current.gameState,
        isFirstMeldTurn: _isFirstMeldTurn,
      );
      SolverLogger.info('UI: search completed (${moves.length} moves)');
      _setOptimalMovesState(OptimalMovesLoaded(moves));
    } catch (error, stackTrace) {
      SolverLogger.warn('UI: search failed — $error');
      SolverLogger.warn('$stackTrace');
      _setOptimalMovesState(OptimalMovesError(error.toString()));
    }
  }

  Future<void> _restoreLastSession() async {
    final saved = await _sessionStorage.loadLastSession();
    if (saved == null) {
      return;
    }
    _isFirstMeldTurn = saved.isFirstMeldTurn;
    _emptyTable = saved.emptyTable;
    _wasSessionRestored = true;
    _setState(SimulationLoaded(saved.gameState));
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
