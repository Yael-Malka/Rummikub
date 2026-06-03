import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../game_engine/domain/entities/move_explanation.dart';
import '../../domain/entities/tile_id.dart';
import 'meld_row.dart';

/// Table melds with rack-tile highlights for move explanation.
class ExplainedTableView extends StatelessWidget {
  const ExplainedTableView({
    required this.phase,
    required this.highlightedTileIds,
    super.key,
  });

  final MoveTablePhase phase;
  final Set<TileId> highlightedTileIds;

  @override
  Widget build(BuildContext context) {
    if (phase.melds.isEmpty) {
      return RtlText(
        AppStrings.emptyTableHint,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final explained in phase.melds)
          MeldRow(
            explained: explained,
            highlightedTileIds: highlightedTileIds,
          ),
      ],
    );
  }
}
