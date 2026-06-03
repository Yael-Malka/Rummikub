import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/constants/solver_constants.dart';
import '../../../../core/widgets/rtl_text.dart';

/// Shown when optimal-move search stopped due to the time limit.
class SearchTimeoutBanner extends StatelessWidget {
  const SearchTimeoutBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final timeout = SolverConstants.searchTimeout;
    final timeoutLabel = timeout.inSeconds >= 1
        ? '${timeout.inSeconds} שניות'
        : '${timeout.inMilliseconds} מ"ש';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer.withValues(alpha: 0.85),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.error,
          width: 1.5,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.timer_off_outlined,
            color: theme.colorScheme.error,
            size: 22,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: RtlText(
              AppStrings.optimalMovesSearchTimedOutMessage(timeoutLabel),
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onErrorContainer,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
