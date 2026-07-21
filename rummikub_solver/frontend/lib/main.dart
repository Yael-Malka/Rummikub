// Boots the app with theme.

import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';

void main() {
  runApp(const RummikubAssistantApp());
}

class RummikubAssistantApp extends StatelessWidget {
  const RummikubAssistantApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rummikub Assistant',
      theme: AppTheme.lightTheme,
      home: const Scaffold(
        body: Center(
          child: Text(
            'Rummikub Assistant',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }
}
