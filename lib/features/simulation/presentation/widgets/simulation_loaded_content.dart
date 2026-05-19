import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../domain/entities/game_state.dart';
import '../providers/simulation_view_model.dart';
import 'rack_view.dart';
import 'table_view.dart';

/// Displays a simulated rack and table.
class SimulationLoadedContent extends StatelessWidget {
  const SimulationLoadedContent({required this.gameState, super.key});

  final GameState gameState;

  @override
  Widget build(BuildContext context) {
    final viewModel = context.read<SimulationViewModel>();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          RackView(tiles: gameState.rack),
          const SizedBox(height: 24),
          TableView(melds: gameState.tableMelds),
          const SizedBox(height: 24),
          AppPrimaryButton(
            label: AppStrings.simulateButton,
            onPressed: viewModel.simulate,
          ),
        ],
      ),
    );
  }
}
