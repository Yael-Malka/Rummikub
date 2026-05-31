import '../../../core/constants/solver_constants.dart';
import '../../../core/services/solver_logger.dart';
import '../../simulation/domain/entities/game_state.dart';
import '../../simulation/domain/entities/meld.dart';
import '../../simulation/domain/entities/tile.dart';
import '../../simulation/domain/entities/tile_id.dart';
import 'entities/move.dart';
import 'legal_meld_generator.dart';
import 'rules_validator.dart';

/// Picks disjoint legal melds to play as many rack tiles as possible.
///
/// Build every legal meld from table + rack, then search for a set where
/// each table tile appears exactly once and each rack tile at most once.
abstract final class SetCoverMoveSolver {
  static List<Move> findOptimalMoves(
    GameState state, {
    required bool isFirstMeldTurn,
    Duration timeout = SolverConstants.searchTimeout,
  }) {
    final rack = List<Tile>.from(state.rack);
    final tableTiles = [
      for (final meld in state.tableMelds) ...meld.tiles,
    ];

    if (tableTiles.isEmpty && rack.isEmpty) {
      return const [];
    }

    if (tableTiles.isEmpty) {
      return _solveOpeningFromRackOnly(
        rack: rack,
        isFirstMeldTurn: isFirstMeldTurn,
        timeout: timeout,
      );
    }

    final search = _TableCoveringSearch(
      state: state,
      rack: rack,
      tableTiles: tableTiles,
      isFirstMeldTurn: isFirstMeldTurn,
      timeout: timeout,
    );
    return search.run();
  }

  /// Empty table: play as many rack tiles as possible into new melds.
  ///
  /// Partial layouts are valid (tiles may remain on the rack). On a first-meld
  /// turn only layouts scoring 30+ from played rack tiles are kept.
  static List<Move> _solveOpeningFromRackOnly({
    required List<Tile> rack,
    required bool isFirstMeldTurn,
    required Duration timeout,
  }) {
    final stopwatch = Stopwatch()..start();
    final legalMelds = LegalMeldGenerator.generateCandidates(rack);

    var bestRackTilesPlayed = -1;
    final bestMoves = <Move>[];

    void saveLayoutIfValid(List<Meld> layout, Set<TileId> tilesInLayout) {
      final count = tilesInLayout.length;
      if (count == 0) {
        return;
      }

      final playedFromRack = layout.expand((m) => m.tiles);
      if (isFirstMeldTurn) {
        final points = RulesValidator.scoreTilesFromRack(playedFromRack);
        if (!RulesValidator.meetsInitialMeldRequirement(points)) {
          return;
        }
      }

      final rackLeft =
          rack.where((t) => !tilesInLayout.contains(t.id)).toList();
      final result = GameState(
        rack: rackLeft,
        tableMelds: List.unmodifiable(layout.map(cloneMeld)),
      );
      if (!RulesValidator.validateGameState(result).isValid) {
        return;
      }

      final move = Move(
        tilesPlayedFromRack: count,
        finalTableMelds: result.tableMelds,
        finalRack: rackLeft,
      );

      if (count > bestRackTilesPlayed) {
        bestRackTilesPlayed = count;
        bestMoves
          ..clear()
          ..add(move);
      } else if (count == bestRackTilesPlayed && !bestMoves.contains(move)) {
        bestMoves.add(move);
      }
    }

    void exploreLayouts(
      List<Meld> layout,
      Set<TileId> tilesInLayout,
      int nextRackIndex,
    ) {
      if (stopwatch.elapsed >= timeout) {
        return;
      }

      saveLayoutIfValid(layout, tilesInLayout);

      final remainingOnRack = rack.length - tilesInLayout.length;
      if (tilesInLayout.length + remainingOnRack <= bestRackTilesPlayed) {
        return;
      }

      while (nextRackIndex < rack.length) {
        final tile = rack[nextRackIndex];
        nextRackIndex++;

        if (tilesInLayout.contains(tile.id)) {
          continue;
        }

        // Leave [tile] on the rack and decide later tiles without using it.
        exploreLayouts(layout, tilesInLayout, nextRackIndex);

        for (final meld in legalMelds) {
          if (!meld.tiles.any((t) => t.id == tile.id)) {
            continue;
          }
          if (!meldIsDisjointFrom(meld, tilesInLayout)) {
            continue;
          }

          for (final meldTile in meld.tiles) {
            tilesInLayout.add(meldTile.id);
          }
          exploreLayouts([...layout, meld], tilesInLayout, nextRackIndex);
          for (final meldTile in meld.tiles) {
            tilesInLayout.remove(meldTile.id);
          }
        }
        return;
      }
    }

    exploreLayouts([], {}, 0);
    return bestMoves;
  }

  static List<Move> _passWithoutPlaying(
    GameState state,
    List<Tile> rack,
  ) {
    if (!RulesValidator.validateGameState(state).isValid) {
      return const [];
    }
    return [
      Move(
        tilesPlayedFromRack: 0,
        finalTableMelds: state.tableMelds,
        finalRack: rack,
      ),
    ];
  }

  static bool meldIsDisjointFrom(Meld meld, Set<TileId> takenTileIds) {
    for (final tile in meld.tiles) {
      if (takenTileIds.contains(tile.id)) {
        return false;
      }
    }
    return true;
  }

  static Meld cloneMeld(Meld meld) {
    return Meld(type: meld.type, tiles: List.unmodifiable(meld.tiles));
  }
}

/// Two-phase search: cover the table first, then add rack-only melds.
final class _TableCoveringSearch {
  _TableCoveringSearch({
    required this.state,
    required this.rack,
    required this.tableTiles,
    required this.isFirstMeldTurn,
    required this.timeout,
  }) : _stopwatch = Stopwatch()..start() {
    _rackTileIds = rack.map((t) => t.id).toSet();
    _tableTileIds = tableTiles.map((t) => t.id).toSet();
    _allTiles = [...tableTiles, ...rack];
  }

  final GameState state;
  final List<Tile> rack;
  final List<Tile> tableTiles;
  final bool isFirstMeldTurn;
  final Duration timeout;

  late final Set<TileId> _rackTileIds;
  late final Set<TileId> _tableTileIds;
  late final List<Tile> _allTiles;
  final Stopwatch _stopwatch;

  late final List<Meld> _legalMelds;
  late final Map<TileId, List<int>> _meldsTouchingTableTile;
  late final List<int> _meldsUsingRackTilesOnly;

  final _takenTileIds = <TileId>{};
  final _layoutSoFar = <Meld>[];

  var _bestRackTilesPlayed = -1;
  final _bestMoves = <Move>[];
  var _nodesExplored = 0;
  var _hitTimeout = false;

  List<Move> run() {
    SolverLogger.info(
      'Set-cover search | rack=${rack.length} tableTiles=${tableTiles.length} '
      'melds=${state.tableMelds.length} firstMeld=$isFirstMeldTurn '
      'timeout=${timeout.inSeconds}s',
    );

    _legalMelds = LegalMeldGenerator.generateCandidates(_allTiles);
    SolverLogger.info('Generated ${_legalMelds.length} candidate melds');

    _meldsTouchingTableTile = {};
    _meldsUsingRackTilesOnly = [];

    for (var i = 0; i < _legalMelds.length; i++) {
      final meld = _legalMelds[i];
      var usesTable = false;

      for (final tile in meld.tiles) {
        if (_tableTileIds.contains(tile.id)) {
          usesTable = true;
          _meldsTouchingTableTile.putIfAbsent(tile.id, () => []).add(i);
        }
      }

      if (!usesTable) {
        _meldsUsingRackTilesOnly.add(i);
      }
    }

    for (final tableTileId in _tableTileIds) {
      if ((_meldsTouchingTableTile[tableTileId] ?? []).isEmpty) {
        SolverLogger.warn('No legal meld covers table tile $tableTileId');
        if (isFirstMeldTurn) {
          return const [];
        }
        return SetCoverMoveSolver._passWithoutPlaying(state, rack);
      }
    }

    coverRemainingTable();

    if (_bestMoves.isEmpty) {
      if (isFirstMeldTurn) {
        SolverLogger.warn('No valid first-meld move (30+ and rack play)');
        return const [];
      }
      final fallback = SetCoverMoveSolver._passWithoutPlaying(state, rack);
      if (fallback.isNotEmpty) {
        SolverLogger.warn('Search found nothing — keeping table as-is');
        return fallback;
      }
    }

    SolverLogger.info(
      'Set-cover done in ${_stopwatch.elapsed.inMilliseconds}ms | '
      'nodes=$_nodesExplored candidates=${_legalMelds.length} '
      'timedOut=$_hitTimeout bestTiles=$_bestRackTilesPlayed solutions=${_bestMoves.length}',
    );

    return _bestMoves;
  }

  bool get _ranTooLong => _stopwatch.elapsed >= timeout;

  /// Phase 1 — every table tile must land in exactly one meld.
  void coverRemainingTable() {
    _nodesExplored++;
    if (_ranTooLong) {
      _hitTimeout = true;
      return;
    }

    final nextTableTile = _firstUncoveredTableTile();
    if (nextTableTile == null) {
      tryAddMeldsFromRack();
      return;
    }

    for (final meldIndex in _meldsTouchingTableTile[nextTableTile]!) {
      final meld = _legalMelds[meldIndex];
      if (!SetCoverMoveSolver.meldIsDisjointFrom(meld, _takenTileIds)) {
        continue;
      }

      _placeMeld(meld);
      coverRemainingTable();
      _removeLastMeld(meld);

      if (_hitTimeout) {
        return;
      }
    }
  }

  /// Phase 2 — table is set; try extra melds built only from the rack.
  void tryAddMeldsFromRack() {
    _nodesExplored++;
    if (_ranTooLong) {
      _hitTimeout = true;
      return;
    }

    saveCurrentLayoutIfValid();

    final rackTilesUsed = _countRackTilesInLayout();
    final rackTilesLeft = _rackTileIds.length - rackTilesUsed;
    if (rackTilesUsed + rackTilesLeft <= _bestRackTilesPlayed) {
      return;
    }

    for (final meldIndex in _meldsUsingRackTilesOnly) {
      final meld = _legalMelds[meldIndex];
      if (!SetCoverMoveSolver.meldIsDisjointFrom(meld, _takenTileIds)) {
        continue;
      }

      _placeMeld(meld);
      tryAddMeldsFromRack();
      _removeLastMeld(meld);

      if (_hitTimeout) {
        return;
      }
    }
  }

  TileId? _firstUncoveredTableTile() {
    for (final tile in tableTiles) {
      if (!_takenTileIds.contains(tile.id)) {
        return tile.id;
      }
    }
    return null;
  }

  int _countRackTilesInLayout() {
    return _takenTileIds.where(_rackTileIds.contains).length;
  }

  void saveCurrentLayoutIfValid() {
    final rackTilesPlayed = _layoutSoFar
        .expand((m) => m.tiles)
        .where((t) => _rackTileIds.contains(t.id))
        .toList();

    final count = rackTilesPlayed.length;

    if (isFirstMeldTurn &&
        !RulesValidator.satisfiesFirstMeldPlay(rackTilesPlayed)) {
      return;
    }

    final rackLeft = rack
        .where((t) => !rackTilesPlayed.any((p) => p.id == t.id))
        .toList();

    final result = GameState(
      rack: rackLeft,
      tableMelds: List.unmodifiable(
        _layoutSoFar.map(SetCoverMoveSolver.cloneMeld),
      ),
    );

    if (!RulesValidator.validateGameState(result).isValid) {
      return;
    }

    final move = Move(
      tilesPlayedFromRack: count,
      finalTableMelds: result.tableMelds,
      finalRack: rackLeft,
    );

    if (count > _bestRackTilesPlayed) {
      _bestRackTilesPlayed = count;
      _bestMoves
        ..clear()
        ..add(move);
      SolverLogger.progress('new best: $count tiles from rack');
    } else if (count == _bestRackTilesPlayed && !_bestMoves.contains(move)) {
      _bestMoves.add(move);
    }
  }

  void _placeMeld(Meld meld) {
    for (final tile in meld.tiles) {
      _takenTileIds.add(tile.id);
    }
    _layoutSoFar.add(meld);
  }

  void _removeLastMeld(Meld meld) {
    for (final tile in meld.tiles) {
      _takenTileIds.remove(tile.id);
    }
    _layoutSoFar.removeLast();
  }
}
