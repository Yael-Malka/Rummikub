import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../providers/auth_view_model.dart';
import 'otp_screen.dart';

class PhoneLoginScreen extends StatefulWidget {
  const PhoneLoginScreen({super.key});

  @override
  State<PhoneLoginScreen> createState() => _PhoneLoginScreenState();
}

class _PhoneLoginScreenState extends State<PhoneLoginScreen> {
  final TextEditingController _phoneController = TextEditingController();
  bool _hasNavigated = false;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Consumer<AuthViewModel>(
            builder: (context, viewModel, _) {
              if (viewModel.verificationId != null &&
                  !viewModel.isSendingCode &&
                  !_hasNavigated) {
                _hasNavigated = true;
                WidgetsBinding.instance.addPostFrameCallback((_) async {
                  if (!mounted || !context.mounted) {
                    return;
                  }
                  await Navigator.of(context).push<void>(
                    MaterialPageRoute<void>(
                      builder: (_) => const OtpScreen(),
                    ),
                  );
                  if (mounted) {
                    setState(() => _hasNavigated = false);
                  }
                });
              }

              if (viewModel.phoneError != null && _hasNavigated) {
                _hasNavigated = false;
              }

              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  RtlText(
                    AppStrings.phoneNumberLabel,
                    style: theme.textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    textDirection: TextDirection.ltr,
                    textAlign: TextAlign.left,
                    decoration: InputDecoration(
                      hintText: AppStrings.phoneHint,
                      hintTextDirection: TextDirection.ltr,
                      errorText: viewModel.phoneError,
                      border: const OutlineInputBorder(),
                    ),
                    onChanged: viewModel.setPhoneInput,
                  ),
                  const SizedBox(height: 24),
                  AppPrimaryButton(
                    label: AppStrings.sendCodeButton,
                    isLoading: viewModel.isSendingCode,
                    onPressed: () async {
                      viewModel.setPhoneInput(_phoneController.text);
                      await viewModel.sendVerificationCode();
                    },
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
