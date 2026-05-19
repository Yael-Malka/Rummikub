import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/theme/tile_palette.dart';
import '../../domain/entities/tile.dart';
import '../../domain/entities/tile_color.dart';

/// Single tile display chip.
class TileChip extends StatelessWidget {
  const TileChip({required this.tile, super.key});

  final Tile tile;

  @override
  Widget build(BuildContext context) {
    final color = tile.color ?? TileColor.joker;
    final label = tile.isJoker ? AppStrings.jokerLabel : '${tile.number}';

    return Container(
      width: 44,
      height: 56,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: TilePalette.background(color),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.outlineVariant,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: TilePalette.foreground(color),
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );
  }
}
