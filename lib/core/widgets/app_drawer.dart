import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../features/auth/domain/usecases/sign_out_use_case.dart';
import '../../features/auth/presentation/providers/auth_view_model.dart';
import '../constants/app_strings.dart';
import 'logout_confirm_dialog.dart';
import 'rtl_text.dart';

/// Side navigation drawer with app actions.
class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  Future<void> _onLogoutTap(BuildContext context) async {
    final confirmed = await showLogoutConfirmDialog(context);
    if (!confirmed || !context.mounted) {
      return;
    }

    Navigator.of(context).pop();

    context.read<AuthViewModel>().resetPhoneAuthState();
    await context.read<SignOutUseCase>()();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Drawer(
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer,
              ),
              child: Align(
                alignment: Alignment.centerRight,
                child: RtlText(
                  AppStrings.appTitle,
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
            ),
            ListTile(
              leading: Icon(
                Icons.logout,
                color: theme.colorScheme.error,
              ),
              title: RtlText(
                AppStrings.logout,
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.error,
                ),
              ),
              onTap: () => _onLogoutTap(context),
            ),
          ],
        ),
      ),
    );
  }
}
