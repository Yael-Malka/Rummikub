import 'package:flutter/material.dart';

class AppSecondaryButton extends StatelessWidget {
  const AppSecondaryButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.isEnabled = true,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isEnabled;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: isEnabled ? onPressed : null,
      child: Text(label),
    );
  }
}
