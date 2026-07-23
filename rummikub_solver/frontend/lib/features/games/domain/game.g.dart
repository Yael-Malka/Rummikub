// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'game.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_Game _$GameFromJson(Map<String, dynamic> json) => _Game(
  id: json['id'] as String,
  userId: json['user_id'] as String,
  name: json['name'] as String,
  description: json['description'] as String?,
  isShared: json['is_shared'] as bool? ?? false,
  createdAt: DateTime.parse(json['created_at'] as String),
  lastUpdated: DateTime.parse(json['last_updated'] as String),
);

Map<String, dynamic> _$GameToJson(_Game instance) => <String, dynamic>{
  'id': instance.id,
  'user_id': instance.userId,
  'name': instance.name,
  'description': instance.description,
  'is_shared': instance.isShared,
  'created_at': instance.createdAt.toIso8601String(),
  'last_updated': instance.lastUpdated.toIso8601String(),
};
