// Email/password login UI.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import 'package:email_validator/email_validator.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../widgets/auth_text_field.dart';
import '../widgets/branded_button.dart';
import '../providers/auth_provider.dart';
import '../../domain/auth_state.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      ref.read(authProvider.notifier).loginWithEmail(
        _emailController.text,
        _passwordController.text,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<AuthState>>(authProvider, (previous, next) {
      if (!next.isLoading && next.hasValue) {
        final state = next.value!;
        if (state.status == AuthStatus.error) {
          // Check for specific error message
          final msg = state.errorMessage ?? '';
          if (msg.contains('not found')) {
            showModalBottomSheet(
              context: context,
              backgroundColor: AppColors.paper50,
              shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.vertical(top: Radius.circular(AppSpacing.radiusXl)),
              ),
              builder: (context) => Padding(
                padding: const EdgeInsets.all(AppSpacing.space6),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      "We don't have an account with that email. Would you like to create one?",
                      style: Theme.of(context).textTheme.bodyLarge,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSpacing.space6),
                    BrandedButton(
                      text: "Create account",
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/register?email=${Uri.encodeComponent(_emailController.text)}');
                      },
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    BrandedButton(
                      text: "Try again",
                      isOutlined: true,
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
            );
          } else if (msg.contains('verify')) {
            context.push('/verify-email?email=${Uri.encodeComponent(_emailController.text)}');
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(msg)),
            );
          }
        }
      } else if (next.hasError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(next.error.toString())),
        );
      }
    });

    final authState = ref.watch(authProvider);
    final isLoading = authState.isLoading || (authState.value?.status == AuthStatus.loading);

    return Scaffold(
      backgroundColor: AppColors.paper100,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.gutterLg),
          child: Container(
            constraints: const BoxConstraints(maxWidth: AppSpacing.contentMax),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SvgPicture.asset(
                    'assets/logos/logo-mark.svg',
                    height: 64,
                  ),
                  const SizedBox(height: AppSpacing.space6),
                  Text(
                    'Sign in',
                    style: Theme.of(context).textTheme.displaySmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.space8),
                  AuthTextField(
                    label: 'Email',
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    validator: (val) {
                      if (val == null || val.isEmpty) return 'Email is required';
                      if (!EmailValidator.validate(val)) return 'Enter a valid email';
                      return null;
                    },
                  ),
                  const SizedBox(height: AppSpacing.space4),
                  AuthTextField(
                    label: 'Password',
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    textInputAction: TextInputAction.done,
                    onFieldSubmitted: (_) => _submit(),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword ? Icons.visibility_off : Icons.visibility,
                        color: AppColors.ink500,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                    validator: (val) {
                      if (val == null || val.isEmpty) return 'Password is required';
                      return null;
                    },
                  ),
                  const SizedBox(height: AppSpacing.space6),
                  BrandedButton(
                    text: 'Sign in',
                    isLoading: isLoading,
                    onPressed: _submit,
                  ),
                  const SizedBox(height: AppSpacing.space8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        "Don't have an account? ",
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      TextButton(
                        onPressed: () => context.push('/register'),
                        child: const Text('Create account'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
