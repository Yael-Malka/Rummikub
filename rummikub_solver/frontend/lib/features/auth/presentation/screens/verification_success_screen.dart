// Post-verification confirmation.

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../widgets/branded_button.dart';

class VerificationSuccessScreen extends StatelessWidget {
  const VerificationSuccessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.paper100,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.gutterLg),
          child: Container(
            constraints: const BoxConstraints(maxWidth: AppSpacing.contentMax),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(
                  Icons.check_circle_outline,
                  size: 64,
                  color: AppColors.success,
                ),
                const SizedBox(height: AppSpacing.space6),
                Text(
                  'Email Verified!',
                  style: Theme.of(context).textTheme.displaySmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space4),
                Text(
                  'Your email has been verified successfully. You can now log in to your account.',
                  style: Theme.of(context).textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space8),
                BrandedButton(
                  text: 'Go to Sign In',
                  onPressed: () => context.go('/login'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
