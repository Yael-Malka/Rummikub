import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';

/// Short in-app guide for the simulation flow.
class HowToUseCard extends StatelessWidget {
  const HowToUseCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              AppStrings.howToTitle,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const Text(AppStrings.howToStep1),
            const SizedBox(height: 4),
            const Text(AppStrings.howToStep2),
            const SizedBox(height: 4),
            const Text(AppStrings.howToStep3),
            const SizedBox(height: 4),
            const Text(AppStrings.howToStep4),
          ],
        ),
      ),
    );
  }
}
