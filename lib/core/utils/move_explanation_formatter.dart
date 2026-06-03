import '../../features/game_engine/domain/entities/move_explanation.dart';
import '../../features/game_engine/domain/joker_role_inferrer.dart';
import '../constants/app_strings.dart';
import 'meld_label_formatter.dart';
import 'tile_label_formatter.dart';

/// Localized strings for [MoveExplanation] (UI layer helper).
abstract final class MoveExplanationFormatter {
  static String formatSummary(MoveExplanationSummary summary) {
    final played = summary.tilesPlayedFromRack;
    final rackLeft = summary.rackTilesRemaining == 0
        ? AppStrings.moveSummaryRackEmpty
        : AppStrings.moveSummaryRackRemaining(summary.rackTilesRemaining);
    return '$played ${AppStrings.moveSummaryPlayedLabel} · $rackLeft';
  }

  static List<String> formatSteps(List<MoveExplanationStep> steps) {
    return [
      for (var i = 0; i < steps.length; i++)
        _formatStep(steps[i], i + 1),
    ];
  }

  static String _formatStep(MoveExplanationStep step, int number) {
    return switch (step) {
      BreakMeldStep(:final beforeMeld) => AppStrings.moveStepBreakMeld(
          number,
          MeldLabelFormatter.formatMeld(
            beforeMeld,
            jokerRoles: JokerRoleInferrer.forMeld(beforeMeld),
          ),
        ),
      BuildMeldStep(:final afterMeld) => AppStrings.moveStepBuildMeld(
          number,
          MeldLabelFormatter.formatMeld(
            afterMeld,
            jokerRoles: JokerRoleInferrer.forMeld(afterMeld),
          ),
        ),
      ExtendMeldStep(:final beforeMeld, :final addedTiles) =>
        AppStrings.moveStepExtendMeld(
          number,
          TileLabelFormatter.formatTiles(addedTiles),
          MeldLabelFormatter.formatMeld(beforeMeld),
        ),
    };
  }
}
