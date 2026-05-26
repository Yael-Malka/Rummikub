import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../features/auth/domain/entities/auth_user.dart';
import '../../features/auth/domain/usecases/observe_auth_state_use_case.dart';
import '../../features/auth/presentation/screens/phone_login_screen.dart';
import '../../features/simulation/presentation/screens/simulation_screen.dart';

/// Routes to login or main content based on phone auth state.
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final observeAuth = context.read<ObserveAuthStateUseCase>();

    return StreamBuilder<AuthUser?>(
      stream: observeAuth(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasData) {
          return const SimulationScreen();
        }

        return const PhoneLoginScreen();
      },
    );
  }
}
