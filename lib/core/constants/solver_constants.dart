/// Limits for move-search performance on device.
abstract final class SolverConstants {
  static const Duration searchTimeout = Duration(seconds: 4);
  static const int maxPartitionsPerPool = 24;
}
