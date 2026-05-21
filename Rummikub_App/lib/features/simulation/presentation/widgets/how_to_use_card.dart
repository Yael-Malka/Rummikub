import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';

/// Short in-app guide for the simulation flow.
class HowToUseCard extends StatelessWidget {
  const HowToUseCard({super.key});

  @override
  Widget build(BuildContext context) {
    final titleStyle = Theme.of(context).textTheme.titleMedium;
    final bodyStyle = Theme.of(context).textTheme.bodyMedium;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RtlText(AppStrings.howToTitle, style: titleStyle),
            const SizedBox(height: 8),
            RtlText(AppStrings.howToStep1, style: bodyStyle),
            const SizedBox(height: 4),
            RtlText(AppStrings.howToStep2, style: bodyStyle),
            const SizedBox(height: 4),
            RtlText(AppStrings.howToStep3, style: bodyStyle),
            const SizedBox(height: 4),
            RtlText(AppStrings.howToStep4, style: bodyStyle),
          ],
        ),
      ),
    );
  }
}
