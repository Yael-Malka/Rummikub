// Registration form UI.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:email_validator/email_validator.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../widgets/auth_text_field.dart';
import '../widgets/branded_button.dart';
import '../providers/auth_provider.dart';
import '../../domain/auth_state.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final emailParam = GoRouterState.of(context).uri.queryParameters['email'];
      if (emailParam != null && emailParam.isNotEmpty) {
        _emailController.text = emailParam;
      }
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      ref.read(authProvider.notifier).register(
        _emailController.text,
        _nameController.text,
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
          final msg = state.errorMessage ?? 'Registration failed';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(msg)),
          );
        } else if (state.status == AuthStatus.unauthenticated &&
            previous?.value?.status == AuthStatus.loading) {
          // Success!
          showDialog(
            context: context,
            barrierDismissible: false,
            builder: (ctx) => AlertDialog(
              backgroundColor: AppColors.paper50,
              title: Text('Account Created', style: Theme.of(context).textTheme.titleLarge),
              content: const Text('Check your inbox: we sent you a verification email.'),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.pop(ctx);
                    context.go('/verify-email?email=${Uri.encodeComponent(_emailController.text)}');
                  },
                  child: const Text('Got it'),
                )
              ],
            ),
          );
        }
      }
    });

    final authState = ref.watch(authProvider);
    final isLoading = authState.maybeWhen(
      data: (state) => state.status == AuthStatus.loading,
      loading: () => true,
      orElse: () => false,
    );

    return Scaffold(
      backgroundColor: AppColors.paper100,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.chevron_left, color: AppColors.ink900, size: 32),
          onPressed: () => context.pop(),
        ),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.gutterLg),
          child: Container(
            constraints: const BoxConstraints(maxWidth: AppSpacing.contentMax),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Create account',
                    style: Theme.of(context).textTheme.displaySmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.space8),
                  AuthTextField(
                    label: 'Full Name',
                    controller: _nameController,
                    textInputAction: TextInputAction.next,
                    validator: (val) {
                      if (val == null || val.isEmpty) return 'Name is required';
                      return null;
                    },
                  ),
                  const SizedBox(height: AppSpacing.space4),
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
                    obscureText: true,
                    textInputAction: TextInputAction.next,
                    validator: (val) {
                      if (val == null || val.isEmpty) return 'Password is required';
                      if (val.length < 8) return 'Must be at least 8 characters';
                      return null;
                    },
                  ),
                  const SizedBox(height: AppSpacing.space4),
                  AuthTextField(
                    label: 'Confirm Password',
                    controller: _confirmPasswordController,
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    onFieldSubmitted: (_) => _submit(),
                    validator: (val) {
                      if (val != _passwordController.text) return 'Passwords do not match';
                      return null;
                    },
                  ),
                  const SizedBox(height: AppSpacing.space8),
                  BrandedButton(
                    text: 'Sign up',
                    isLoading: isLoading,
                    onPressed: _submit,
                  ),
                  const SizedBox(height: AppSpacing.space6),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
