import 'package:flutter/material.dart';

import '../constants/app_strings.dart';
import 'rtl_text.dart';

/// Shows a Hebrew confirmation dialog before signing out.
Future<bool> showLogoutConfirmDialog(BuildContext context) {
  return showDialog<bool>(
    context: context,
    builder: (dialogContext) {
      return AlertDialog(
        title: const RtlText(AppStrings.logoutDialogTitle),
        content: const RtlText(AppStrings.logoutDialogMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const RtlText(AppStrings.logoutCancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const RtlText(AppStrings.logoutConfirm),
          ),
        ],
      );
    },
  ).then((value) => value ?? false);
}
