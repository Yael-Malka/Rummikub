// Turn metadata and lifecycle status.

enum TurnStatus { create }

class Turn {
  final String id;
  final String gameId;
  final String name;
  final String? description;
  final DateTime createdAt;
  final TurnStatus status;
  final bool isFirstDrop;

  const Turn({
    required this.id,
    required this.gameId,
    required this.name,
    this.description,
    required this.createdAt,
    required this.status,
    this.isFirstDrop = false,
  });

  factory Turn.fromJson(Map<String, dynamic> json) {
    return Turn(
      id: json['id'] as String,
      gameId: json['gameId'] as String,
      name: json['name'] as String? ?? 'Unnamed Turn',
      description: json['description'] as String?,
      createdAt: json['createdAt'] != null
          ? DateTime.parse(json['createdAt'] as String)
          : (json['timestamp'] != null
              ? DateTime.parse(json['timestamp'] as String)
              : DateTime.now()),
      status: TurnStatus.values.firstWhere(
        (status) => status.name == (json['status'] as String).toLowerCase(),
        orElse: () => TurnStatus.create,
      ),
      isFirstDrop: json['isFirstDrop'] as bool? ?? false,
    );
  }
}
