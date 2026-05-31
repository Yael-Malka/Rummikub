import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../providers/simulation_view_model.dart';

/// Generation options shown before and after simulating.
class SimulationOptionsPanel extends StatelessWidget {
  const SimulationOptionsPanel({
    this.disableControls = false,
    super.key,
  });

  final bool disableControls;

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<SimulationViewModel>();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text(AppStrings.emptyTableToggleLabel),
          subtitle: const Text(AppStrings.emptyTableToggleSubtitle),
          value: viewModel.emptyTable,
          onChanged:
              disableControls ? null : viewModel.setEmptyTable,
        ),
      ],
    );
  }
}
