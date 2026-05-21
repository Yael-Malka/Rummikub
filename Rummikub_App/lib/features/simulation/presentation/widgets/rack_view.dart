import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../domain/entities/tile.dart';
import 'tile_chip.dart';

/// Player rack tiles.
class RackView extends StatelessWidget {
  const RackView({required this.tiles, super.key});

  final List<Tile> tiles;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RtlText(
          '${AppStrings.rackTitle} — ${tiles.length} ${AppStrings.rackCountLabel}',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [for (final tile in tiles) TileChip(tile: tile)],
        ),
      ],
    );
  }
}
