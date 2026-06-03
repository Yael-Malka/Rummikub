import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/utils/move_explanation_formatter.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../game_engine/domain/entities/move_explanation.dart';
import '../../domain/entities/tile_id.dart';
import 'explained_table_view.dart';

/// Result of one optimal move: summary, after-table only, optional text steps.
class MoveExplanationPanel extends StatefulWidget {
  const MoveExplanationPanel({
    required this.explanation,
    super.key,
  });

  final MoveExplanation explanation;

  @override
  State<MoveExplanationPanel> createState() => _MoveExplanationPanelState();
}

class _MoveExplanationPanelState extends State<MoveExplanationPanel> {
  var _showTextSteps = false;

  @override
  Widget build(BuildContext context) {
    final explanation = widget.explanation;
    final theme = Theme.of(context);
    final highlights = explanation.highlightedRackTileIds;
    final stepLabels = MoveExplanationFormatter.formatSteps(explanation.steps);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SummaryBanner(summary: explanation.summary),
        const SizedBox(height: 12),
        _PhaseSection(
          label: AppStrings.finalTableTitle,
          phase: explanation.after,
          highlightedTileIds: highlights,
        ),
        if (stepLabels.isNotEmpty) ...[
          const SizedBox(height: 12),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton.icon(
              onPressed: () => setState(() => _showTextSteps = !_showTextSteps),
              icon: Icon(_showTextSteps ? Icons.visibility : Icons.menu_book),
              label: RtlText(
                _showTextSteps
                    ? AppStrings.moveHideTextSteps
                    : AppStrings.moveShowTextSteps,
              ),
            ),
          ),
          if (_showTextSteps) ...[
            const SizedBox(height: 4),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest
                    .withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: theme.colorScheme.outlineVariant),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  RtlText(
                    AppStrings.moveStepsTitle,
                    style: theme.textTheme.titleSmall,
                  ),
                  const SizedBox(height: 8),
                  for (final label in stepLabels)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: RtlText(
                        label,
                        style: theme.textTheme.bodyMedium,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ],
    );
  }
}

class _SummaryBanner extends StatelessWidget {
  const _SummaryBanner({required this.summary});

  final MoveExplanationSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      child: Center(
        child: _StatChip(
          value: '${summary.tilesPlayedFromRack}',
          label: AppStrings.moveSummaryPlayedLabel,
        ),
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  const _StatChip({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        RtlText(
          label,
          style: Theme.of(context).textTheme.labelSmall,
        ),
      ],
    );
  }
}

class _PhaseSection extends StatelessWidget {
  const _PhaseSection({
    required this.label,
    required this.phase,
    required this.highlightedTileIds,
  });

  final String label;
  final MoveTablePhase phase;
  final Set<TileId> highlightedTileIds;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outlineVariant,
          width: 1.5,
        ),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RtlText(
              label,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            ExplainedTableView(
              phase: phase,
              highlightedTileIds: highlightedTileIds,
            ),
          ],
        ),
      ),
    );
  }
}
