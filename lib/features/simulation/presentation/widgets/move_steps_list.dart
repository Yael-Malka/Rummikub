import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../../core/utils/move_step_formatter.dart';
import '../../../game_engine/domain/entities/move_step.dart';

class MoveStepsList extends StatelessWidget {
  const MoveStepsList({required this.steps, super.key});

  final List<MoveStep> steps;

  @override
  Widget build(BuildContext context) {
    if (steps.isEmpty) {
      return const SizedBox.shrink();
    }

    final labels = MoveStepFormatter.formatSteps(steps);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RtlText(
          AppStrings.moveStepsTitle,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        for (final label in labels)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: RtlText(label),
          ),
      ],
    );
  }
}
