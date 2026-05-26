import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/app_secondary_button.dart';
import '../../domain/entities/game_state.dart';
import '../providers/simulation_view_model.dart';
import '../state/optimal_moves_state.dart';
import 'optimal_moves_section.dart';
import 'rack_view.dart';
import 'saved_session_banner.dart';
import 'table_view.dart';

/// Displays a simulated rack and table.
class SimulationLoadedContent extends StatelessWidget {
  const SimulationLoadedContent({required this.gameState, super.key});

  final GameState gameState;

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<SimulationViewModel>();
    final isSearchingMoves =
        viewModel.optimalMovesState is OptimalMovesLoading;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (viewModel.wasSessionRestored) const SavedSessionBanner(),
          RackView(tiles: gameState.rack),
          const SizedBox(height: 24),
          TableView(melds: gameState.tableMelds),
          const SizedBox(height: 16),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text(AppStrings.firstMeldToggleLabel),
            value: viewModel.isFirstMeldTurn,
            onChanged: isSearchingMoves ? null : viewModel.setFirstMeldTurn,
          ),
          AppSecondaryButton(
            label: AppStrings.showOptimalMovesButton,
            isEnabled: !isSearchingMoves,
            isLoading: isSearchingMoves,
            loadingLabel: AppStrings.computingOptimalMovesMessage,
            onPressed: viewModel.findOptimalMoves,
          ),
          OptimalMovesSection(
            movesState: viewModel.optimalMovesState,
            stateBefore: gameState,
          ),
          const SizedBox(height: 24),
          AppPrimaryButton(
            label: AppStrings.simulateButton,
            isEnabled: !isSearchingMoves,
            onPressed: viewModel.simulate,
          ),
        ],
      ),
    );
  }
}
