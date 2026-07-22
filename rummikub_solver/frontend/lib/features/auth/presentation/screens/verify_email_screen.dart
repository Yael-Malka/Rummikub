// Prompt to verify email.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../widgets/branded_button.dart';
import '../providers/auth_provider.dart';

class VerifyEmailScreen extends ConsumerWidget {
  const VerifyEmailScreen({super.key});

  Future<void> _openEmailApp() async {
    final Uri emailLaunchUri = Uri(
      scheme: 'mailto',
    );
    if (await canLaunchUrl(emailLaunchUri)) {
      await launchUrl(emailLaunchUri);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final email = GoRouterState.of(context).uri.queryParameters['email'] ?? 'your email';

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
                  Icons.mark_email_read_outlined,
                  size: 64,
                  color: AppColors.brand,
                ),
                const SizedBox(height: AppSpacing.space6),
                Text(
                  'Verify your email',
                  style: Theme.of(context).textTheme.displaySmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space4),
                Text(
                  'We sent a verification email to $email. Check your inbox and tap the link to verify.',
                  style: Theme.of(context).textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space8),
                BrandedButton(
                  text: 'Open email app',
                  isOutlined: true,
                  onPressed: _openEmailApp,
                ),
                const SizedBox(height: AppSpacing.space4),
                TextButton(
                  onPressed: () async {
                    if (email != 'your email') {
                      try {
                        await ref.read(authProvider.notifier).resendVerificationEmail(email);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Verification email resent!')),
                          );
                        }
                      } catch (e) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Failed to resend email.')),
                          );
                        }
                      }
                    }
                  },
                  child: const Text('Resend email'),
                ),
                const SizedBox(height: AppSpacing.space2),
                TextButton(
                  onPressed: () => context.go('/login'),
                  child: const Text('Back to sign in'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
