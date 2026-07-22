// Primary action button.

import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class BrandedButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isOutlined;
  final bool isLoading;

  const BrandedButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isOutlined = false,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final Widget child = isLoading
        ? const SizedBox(
            height: 20,
            width: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: AppColors.white,
            ),
          )
        : Text(text);

    if (isOutlined) {
      return OutlinedButton(
        onPressed: isLoading ? null : onPressed,
        child: isLoading 
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.brand,
                ),
              )
            : child,
      );
    }

    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      child: child,
    );
  }
}
