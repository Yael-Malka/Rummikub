// Consistent snackbars across screens.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';

enum SnackbarType { error, success, info }

class AppSnackbar {
  static void show(
    BuildContext context, {
    required String message,
    SnackbarType type = SnackbarType.info,
  }) {
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    scaffoldMessenger.hideCurrentSnackBar();

    Color backgroundColor;
    switch (type) {
      case SnackbarType.error:
        backgroundColor = AppColors.danger;
        break;
      case SnackbarType.success:
        backgroundColor = AppColors.success;
        break;
      case SnackbarType.info:
        backgroundColor = AppColors.info;
        break;
    }

    scaffoldMessenger.showSnackBar(
      SnackBar(
        content: Text(
          message,
          style: GoogleFonts.hankenGrotesk(color: AppColors.white),
        ),
        backgroundColor: backgroundColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
        ),
        elevation: 5,
        margin: const EdgeInsets.all(AppSpacing.gutterLg),
      ),
    );
  }
}
