import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../game_engine/domain/entities/move_explanation.dart';
import '../../domain/entities/meld_type.dart';
import '../../domain/entities/tile_id.dart';
import 'tile_chip.dart';

/// One meld row on the table (with optional highlights and joker hints).
class MeldRow extends StatelessWidget {
  const MeldRow({
    required this.explained,
    required this.highlightedTileIds,
    super.key,
  });

  final ExplainedMeld explained;
  final Set<TileId> highlightedTileIds;

  @override
  Widget build(BuildContext context) {
    final meld = explained.meld;
    final typeLabel = switch (meld.type) {
      MeldType.group => AppStrings.meldGroupLabel,
      MeldType.run => AppStrings.meldRunLabel,
    };

    JokerRole? roleFor(TileId id) {
      for (final role in explained.jokerRoles) {
        if (role.jokerTileId == id) {
          return role;
        }
      }
      return null;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          RtlText(
            typeLabel,
            style: Theme.of(context).textTheme.labelMedium,
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final tile in meld.tiles)
                TileChip(
                  tile: tile,
                  isHighlighted: highlightedTileIds.contains(tile.id),
                  jokerRole: roleFor(tile.id),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
