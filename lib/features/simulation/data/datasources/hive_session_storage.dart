import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

import '../../../../core/services/session_storage.dart';
import '../models/game_state_codec.dart';
import '../models/saved_session.dart';

/// Hive-backed persistence for the last simulation session.
final class HiveSessionStorage implements SessionStorage {
  HiveSessionStorage({Box<String>? box}) : _box = box;

  static const String boxName = 'rummikub_session';
  static const String lastSessionKey = 'last_session';

  Box<String>? _box;

  Future<Box<String>> _openBox() async {
    _box ??= await Hive.openBox<String>(boxName);
    return _box!;
  }

  @override
  Future<void> clearLastSession() async {
    final box = await _openBox();
    await box.delete(lastSessionKey);
  }

  @override
  Future<SavedSession?> loadLastSession() async {
    final box = await _openBox();
    final raw = box.get(lastSessionKey);
    if (raw == null) {
      return null;
    }
    try {
      final json = jsonDecode(raw);
      if (json is! Map) {
        return null;
      }
      return GameStateCodec.decodeSession(Map<String, dynamic>.from(json));
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> saveLastSession(SavedSession session) async {
    final box = await _openBox();
    final encoded = jsonEncode(GameStateCodec.encodeSession(session));
    await box.put(lastSessionKey, encoded);
  }
}
