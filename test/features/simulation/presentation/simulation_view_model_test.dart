import 'package:flutter_test/flutter_test.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/state/simulation_state.dart';

void main() {
  group('SimulationViewModel', () {
    test('givenNewInstance_whenCreated_thenStateIsInitial', () {
      final viewModel = SimulationViewModel();

      expect(viewModel.state, isA<SimulationInitial>());
    });

    test('givenInitialState_whenSimulate_thenStateRemainsInitial', () async {
      final viewModel = SimulationViewModel();

      await viewModel.simulate();

      expect(viewModel.state, isA<SimulationInitial>());
    });
  });
}
