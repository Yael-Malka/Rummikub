import '../../features/game_engine/domain/entities/move_step.dart';
import '../constants/app_strings.dart';
import 'tile_label_formatter.dart';

/// Converts [MoveStep] values into localized UI strings.
abstract final class MoveStepFormatter {
  static List<String> formatSteps(List<MoveStep> steps) {
    return [
      for (var index = 0; index < steps.length; index++)
        _formatStep(steps[index], index + 1),
    ];
  }

  static String _formatStep(MoveStep step, int stepNumber) {
    return switch (step) {
      PlayTilesFromRackStep(:final tiles) =>
        '$stepNumber. ${AppStrings.moveStepPlayFromRack(TileLabelFormatter.formatTiles(tiles))}',
      ReorganizeTableStep(
        :final meldsBeforeCount,
        :final meldsAfterCount,
      ) =>
        '$stepNumber. ${AppStrings.moveStepReorganizeTable(meldsBeforeCount, meldsAfterCount)}',
    };
  }
}
