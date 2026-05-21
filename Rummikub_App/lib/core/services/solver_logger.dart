import 'package:flutter/foundation.dart';

/// Debug logging for move-search progress (visible in `flutter run` / Logcat).
abstract final class SolverLogger {
  static const String _tag = 'RummikubSolver';

  static void info(String message) {
    debugPrint('[$_tag] $message');
  }

  static void progress(String message) {
    debugPrint('[$_tag] … $message');
  }

  static void warn(String message) {
    debugPrint('[$_tag] ⚠ $message');
  }
}
