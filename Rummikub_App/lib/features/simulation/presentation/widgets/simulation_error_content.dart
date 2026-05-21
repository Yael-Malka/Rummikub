import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../providers/simulation_view_model.dart';

/// Error state with retry.
class SimulationErrorContent extends StatelessWidget {
  const SimulationErrorContent({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    final viewModel = context.read<SimulationViewModel>();

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RtlText(
              message,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Theme.of(context).colorScheme.error,
                  ),
            ),
            const SizedBox(height: 24),
            AppPrimaryButton(
              label: AppStrings.retryButton,
              onPressed: viewModel.simulate,
            ),
          ],
        ),
      ),
    );
  }
}
