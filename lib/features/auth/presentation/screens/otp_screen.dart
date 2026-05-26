import 'package:flutter/material.dart';
import 'package:pinput/pinput.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/constants/auth_constants.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../simulation/presentation/screens/simulation_screen.dart';
import '../providers/auth_view_model.dart';

class OtpScreen extends StatelessWidget {
  const OtpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    final defaultPinTheme = PinTheme(
      width: 56,
      height: 56,
      textStyle: theme.textTheme.headlineSmall,
      decoration: BoxDecoration(
        border: Border.all(color: colorScheme.outline),
        borderRadius: BorderRadius.circular(8),
      ),
    );

    final focusedPinTheme = defaultPinTheme.copyWith(
      decoration: defaultPinTheme.decoration?.copyWith(
        border: Border.all(color: colorScheme.primary, width: 2),
      ),
    );

    final errorPinTheme = defaultPinTheme.copyWith(
      decoration: defaultPinTheme.decoration?.copyWith(
        border: Border.all(color: colorScheme.error),
      ),
    );

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            context.read<AuthViewModel>().resetPhoneAuthState();
            Navigator.of(context).pop();
          },
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Consumer<AuthViewModel>(
            builder: (context, viewModel, _) {
              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  RtlText(
                    AppStrings.otpPrompt,
                    style: theme.textTheme.titleLarge,
                    maxLines: 2,
                  ),
                  const SizedBox(height: 32),
                  Directionality(
                    textDirection: TextDirection.ltr,
                    child: Pinput(
                      length: AuthConstants.otpLength,
                      defaultPinTheme: defaultPinTheme,
                      focusedPinTheme: focusedPinTheme,
                      errorPinTheme: errorPinTheme,
                      forceErrorState: viewModel.otpError != null,
                      keyboardType: TextInputType.number,
                      onChanged: viewModel.setOtpCode,
                    ),
                  ),
                  if (viewModel.otpError != null) ...[
                    const SizedBox(height: 12),
                    RtlText(
                      viewModel.otpError!,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: colorScheme.error,
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  AppPrimaryButton(
                    label: AppStrings.verifyButton,
                    isLoading: viewModel.isVerifyingOtp,
                    onPressed: () async {
                      final success = await viewModel.verifyOtpCode();
                      if (!success || !context.mounted) {
                        return;
                      }

                      viewModel.resetPhoneAuthState();
                      await Navigator.of(context).pushAndRemoveUntil<void>(
                        MaterialPageRoute<void>(
                          builder: (_) => const SimulationScreen(),
                        ),
                        (_) => false,
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: viewModel.canResendCode
                        ? viewModel.resendCode
                        : null,
                    child: RtlText(
                      viewModel.canResendCode
                          ? AppStrings.resendCode
                          : AppStrings.resendCodeCountdown(
                              viewModel.resendCooldownSeconds,
                            ),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: viewModel.canResendCode
                            ? colorScheme.primary
                            : colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
