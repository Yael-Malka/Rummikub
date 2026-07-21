// Full-screen loading spinner.

import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class LoadingOverlay extends StatelessWidget {
  final bool isLoading;
  final Widget child;

  const LoadingOverlay({
    super.key,
    required this.isLoading,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: AppColors.ink900.withValues(alpha: 0.3),
            child: const Center(
              child: CircularProgressIndicator(
                color: AppColors.brand,
              ),
            ),
          ),
      ],
    );
  }
}
