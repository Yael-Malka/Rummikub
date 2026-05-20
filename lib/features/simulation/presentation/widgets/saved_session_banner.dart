import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';

class SavedSessionBanner extends StatelessWidget {
  const SavedSessionBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: AppStrings.savedSessionBanner,
      child: MaterialBanner(
        content: const Text(AppStrings.savedSessionBanner),
        leading: Icon(
          Icons.restore,
          color: Theme.of(context).colorScheme.primary,
        ),
        actions: const [SizedBox.shrink()],
      ),
    );
  }
}
