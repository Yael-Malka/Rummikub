import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../providers/simulation_view_model.dart';

/// Welcome state with simulate action.
class SimulationInitialContent extends StatelessWidget {
  const SimulationInitialContent({super.key});

  @override
  Widget build(BuildContext context) {
    final viewModel = context.read<SimulationViewModel>();

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              AppStrings.welcomeMessage,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            AppPrimaryButton(
              label: AppStrings.simulateButton,
              onPressed: viewModel.simulate,
            ),
          ],
        ),
      ),
    );
  }
}
