import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/theme/rack_played_highlight.dart';
import '../../../../core/theme/tile_palette.dart';
import '../../../../core/utils/tile_label_formatter.dart';
import '../../domain/entities/tile.dart';
import '../../domain/entities/tile_color.dart';
import '../../../game_engine/domain/entities/move_explanation.dart';

/// Single tile display chip.
class TileChip extends StatelessWidget {
  const TileChip({
    required this.tile,
    this.isHighlighted = false,
    this.jokerRole,
    super.key,
  });

  final Tile tile;
  final bool isHighlighted;
  final JokerRole? jokerRole;

  @override
  Widget build(BuildContext context) {
    final color = tile.color ?? TileColor.joker;
    final scheme = Theme.of(context).colorScheme;
    final numberLabel = tile.isJoker ? AppStrings.jokerLabel : '${tile.number}';
    final jokerSubtext = _jokerSubtext();

    Widget chip = Container(
      width: 44,
      height: 56,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: TilePalette.background(color),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isHighlighted
              ? RackPlayedHighlight.border
              : scheme.outlineVariant,
          width: isHighlighted ? RackPlayedHighlight.borderWidth : 1,
        ),
        boxShadow: isHighlighted
            ? const [
                BoxShadow(
                  color: Colors.black26,
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: Text(
        numberLabel,
        style: TextStyle(
          color: TilePalette.foreground(color),
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );

    if (isHighlighted) {
      chip = Container(
        padding: const EdgeInsets.all(RackPlayedHighlight.outerRingWidth),
        decoration: BoxDecoration(
          color: RackPlayedHighlight.outerRing,
          borderRadius: BorderRadius.circular(10),
        ),
        child: chip,
      );
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        chip,
        if (isHighlighted) ...[
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            decoration: BoxDecoration(
              color: RackPlayedHighlight.border,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              AppStrings.rackPlayedBadge,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 9,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
        if (jokerSubtext != null) ...[
          const SizedBox(height: 2),
          Text(
            jokerSubtext,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontSize: 10,
                ),
            textAlign: TextAlign.center,
          ),
        ],
      ],
    );
  }

  String? _jokerSubtext() {
    if (!tile.isJoker || jokerRole == null) {
      return null;
    }
    final role = jokerRole!;
    if (role.standsInForColor != null) {
      return '→ ${TileLabelFormatter.formatTileLabel(
        role.standsInForColor!,
        role.standsInForNumber,
      )}';
    }
    return '→ ${role.standsInForNumber}';
  }
}
