import '../../features/simulation/data/models/saved_session.dart';

/// Persists the last simulated game on device.
abstract interface class SessionStorage {
  Future<SavedSession?> loadLastSession();

  Future<void> saveLastSession(SavedSession session);

  Future<void> clearLastSession();
}

/// No persistence — used in tests.
final class NoOpSessionStorage implements SessionStorage {
  const NoOpSessionStorage();

  @override
  Future<void> clearLastSession() async {}

  @override
  Future<SavedSession?> loadLastSession() async => null;

  @override
  Future<void> saveLastSession(SavedSession session) async {}
}
