// Declares routes and redirects unauthenticated users to login.

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/auth/domain/auth_state.dart';
import '../../features/auth/presentation/screens/verify_email_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/auth/presentation/screens/verification_success_screen.dart';
import '../../features/games/presentation/pages/games_page.dart';

part 'app_router.g.dart';

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;
  RouterNotifier(this._ref) {
    _ref.listen<AsyncValue<AuthState>>(
      authProvider,
      (_, __) => notifyListeners(),
    );
  }
}

@riverpod
GoRouter appRouter(Ref ref) {
  final notifier = RouterNotifier(ref);

  return GoRouter(
    initialLocation: '/home',
    refreshListenable: notifier,
    redirect: (context, state) {
      final authStateAsync = ref.read(authProvider);
      if (authStateAsync is AsyncLoading) return null;
      
      final authState = authStateAsync.value;
      final isAuthenticated = authState?.status == AuthStatus.authenticated;
      
      final isLoginRoute = state.uri.path == '/login';
      final isRegisterRoute = state.uri.path == '/register';
      final isVerifyRoute = state.uri.path.startsWith('/verify');

      if (!isAuthenticated && !isLoginRoute && !isRegisterRoute && !isVerifyRoute) {
        return '/login';
      }

      if (isAuthenticated && (isLoginRoute || isRegisterRoute)) {
        return '/home';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/verify-email',
        builder: (context, state) => const VerifyEmailScreen(),
      ),
      GoRoute(
        path: '/verify-success',
        builder: (context, state) => const VerificationSuccessScreen(),
      ),
      GoRoute(
        path: '/verify',
        builder: (context, state) {
          final token = state.uri.queryParameters['token'];
          if (token != null) {
            WidgetsBinding.instance.addPostFrameCallback((_) async {
              try {
                await ref.read(authProvider.notifier).verifyEmail(token);
                if (context.mounted) {
                  context.go('/verify-success');
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('This link is invalid or has expired.')),
                  );
                }
              }
            });
          }
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        },
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const GamesPage(),
      ),
    ],
  );
}
