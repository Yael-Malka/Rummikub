import 'package:flutter/material.dart';

import '../constants/app_strings.dart';
import 'rtl_text.dart';

/// Loading row with spinner and Hebrew status text.
class ComputingIndicator extends StatelessWidget {
  const ComputingIndicator({
    required this.message,
    super.key,
  });

  final String message;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Semantics(
      label: message,
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: colorScheme.primary,
              ),
            ),
            const SizedBox(width: 16),
            Flexible(
              child: RtlText(
                message,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: colorScheme.primary,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Shown while optimal moves are calculated.
class OptimalMovesComputingIndicator extends StatelessWidget {
  const OptimalMovesComputingIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return const ComputingIndicator(
      message: AppStrings.computingOptimalMovesMessage,
    );
  }
}
