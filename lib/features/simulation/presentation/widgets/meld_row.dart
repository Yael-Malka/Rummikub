import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../domain/entities/meld.dart';
import '../../domain/entities/meld_type.dart';
import 'tile_chip.dart';

/// One meld row on the table.
class MeldRow extends StatelessWidget {
  const MeldRow({required this.meld, super.key});

  final Meld meld;

  @override
  Widget build(BuildContext context) {
    final typeLabel = switch (meld.type) {
      MeldType.group => AppStrings.meldGroupLabel,
      MeldType.run => AppStrings.meldRunLabel,
    };

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
              for (final tile in meld.tiles) TileChip(tile: tile),
            ],
          ),
        ],
      ),
    );
  }
}
