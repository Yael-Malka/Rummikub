import 'package:flutter/foundation.dart';

import '../../domain/exceptions/state_generation_exception.dart';
import '../../domain/usecases/generate_simulated_state_use_case.dart';
import '../state/simulation_state.dart';

/// ViewModel for simulation flow.
class SimulationViewModel extends ChangeNotifier {
  SimulationViewModel(this._generateSimulatedState);

  final GenerateSimulatedStateUseCase _generateSimulatedState;

  SimulationState _state = const SimulationInitial();

  SimulationState get state => _state;

  Future<void> simulate() async {
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

  void _setState(SimulationState newState) {
    _state = newState;
    notifyListeners();
  }
}
