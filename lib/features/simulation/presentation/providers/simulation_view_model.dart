import 'package:flutter/foundation.dart';

import '../state/simulation_state.dart';

/// ViewModel for simulation flow. Orchestrates use cases in later phases.
class SimulationViewModel extends ChangeNotifier {
  SimulationState _state = const SimulationInitial();

  SimulationState get state => _state;

  void _setState(SimulationState newState) {
    _state = newState;
    notifyListeners();
  }

  /// Placeholder for phase 4+ — will call [GenerateSimulatedStateUseCase].
  Future<void> simulate() async {
    // No-op in phase 1; wired in phase 5.
    _setState(_state);
  }
}
