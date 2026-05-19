import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../providers/simulation_view_model.dart';
import '../state/simulation_state.dart';
import '../widgets/simulation_error_content.dart';
import '../widgets/simulation_initial_content.dart';
import '../widgets/simulation_loaded_content.dart';

class SimulationScreen extends StatelessWidget {
  const SimulationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<SimulationViewModel>();

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.simulationScreenTitle),
      ),
      body: switch (viewModel.state) {
        SimulationInitial() => const SimulationInitialContent(),
        SimulationLoading() => const Center(
            child: CircularProgressIndicator(),
          ),
        SimulationLoaded(:final gameState) => SimulationLoadedContent(
            gameState: gameState,
          ),
        SimulationError(:final message) => SimulationErrorContent(
            message: message,
          ),
      },
    );
  }
}
