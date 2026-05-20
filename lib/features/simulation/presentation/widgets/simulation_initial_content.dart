import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../providers/simulation_view_model.dart';
import 'how_to_use_card.dart';

/// Welcome state with simulate action.
class SimulationInitialContent extends StatelessWidget {
  const SimulationInitialContent({super.key});

  @override
  Widget build(BuildContext context) {
    final viewModel = context.read<SimulationViewModel>();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            AppStrings.welcomeMessage,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 24),
          const HowToUseCard(),
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
