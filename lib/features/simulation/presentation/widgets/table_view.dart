import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../domain/entities/meld.dart';
import 'meld_row.dart';

/// Table melds display.
class TableView extends StatelessWidget {
  const TableView({required this.melds, super.key});

  final List<Meld> melds;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RtlText(
          '${AppStrings.tableTitle} — ${melds.length} ${AppStrings.tableMeldsLabel}',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        if (melds.isEmpty)
          RtlText(
            AppStrings.emptyTableHint,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          )
        else
          for (final meld in melds) MeldRow(meld: meld),
      ],
    );
  }
}
