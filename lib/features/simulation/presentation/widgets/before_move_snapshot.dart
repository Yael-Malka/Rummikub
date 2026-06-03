import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../domain/entities/game_state.dart';
import 'rack_view.dart';
import 'table_view.dart';

/// Shared table + rack state shown once above all optimal-move options.
class BeforeMoveSnapshot extends StatelessWidget {
  const BeforeMoveSnapshot({required this.stateBefore, super.key});

  final GameState stateBefore;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RtlText(
              AppStrings.optimalMovesBeforeStateTitle,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            RtlText(
              AppStrings.beforeTableTitle,
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            TableView(melds: stateBefore.tableMelds),
            const SizedBox(height: 12),
            RtlText(
              AppStrings.beforeRackTitle,
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            RackView(tiles: stateBefore.rack),
          ],
        ),
      ),
    );
  }
}
