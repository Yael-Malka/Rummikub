// Styled text field for auth forms.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

class AuthTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final bool obscureText;
  final Widget? suffixIcon;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final void Function(String)? onFieldSubmitted;
  final String? initialValue;

  const AuthTextField({
    super.key,
    required this.label,
    this.hint,
    this.obscureText = false,
    this.suffixIcon,
    this.controller,
    this.validator,
    this.keyboardType,
    this.textInputAction,
    this.onFieldSubmitted,
    this.initialValue,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.hankenGrotesk(
            color: AppColors.ink500,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: AppSpacing.space2),
        SizedBox(
          child: TextFormField(
            controller: controller,
            initialValue: initialValue,
            obscureText: obscureText,
            validator: validator,
            keyboardType: keyboardType,
            textInputAction: textInputAction,
            onFieldSubmitted: onFieldSubmitted,
            style: GoogleFonts.hankenGrotesk(color: AppColors.ink900),
            decoration: InputDecoration(
              hintText: hint,
              suffixIcon: suffixIcon,
            ),
          ),
        ),
      ],
    );
  }
}
