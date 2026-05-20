/// Centralized UI strings (single source of truth).
abstract final class AppStrings {
  static const String appTitle = 'Rummikub Assistant';
  static const String simulationScreenTitle = 'סימולציית משחק';
  static const String welcomeMessage =
      'לחצי על הכפתור להגרלת תושבת ושולחן אקראיים (חוקיים).';
  static const String simulateButton = 'סימולציית מצב';
  static const String rackTitle = 'תושבת';
  static const String tableTitle = 'שולחן';
  static const String rackCountLabel = 'אבנים בתושבת';
  static const String tableMeldsLabel = 'סטים על השולחן';
  static const String meldGroupLabel = 'קבוצה';
  static const String meldRunLabel = 'רצף';
  static const String jokerLabel = 'J';
  static const String retryButton = 'נסי שוב';
  static const String firstMeldToggleLabel = 'ריצוי ראשון (מינימום 30 נקודות)';
  static const String showOptimalMovesButton = 'הצג מהלכים אופטימליים';
  static const String optimalMovesTitle = 'מהלכים אופטימליים';
  static const String noOptimalMovesMessage = 'אין מהלך חוקי מהתושבת';
  static const String moveNumberLabel = 'מהלך';
  static const String tilesPlayedFromRackLabel = 'אבנים מהתושבת';
  static const String finalRackTitle = 'תושבת אחרי המהלך';
  static const String finalTableTitle = 'שולחן אחרי המהלך';
  static const String beforeRackTitle = 'תושבת לפני המהלך';
  static const String beforeTableTitle = 'שולחן לפני המהלך';
  static const String moveStepsTitle = 'צעדי המהלך';
  static const String jokerTileName = "ג'וקר";
  static const String colorRed = 'אדום';
  static const String colorBlue = 'כחול';
  static const String colorBlack = 'שחור';
  static const String colorOrange = 'כתום';
  static const String savedSessionBanner =
      'נטען מצב משחק אחרון שנשמר במכשיר';
  static const String howToTitle = 'איך משתמשים';
  static const String howToStep1 = '1. לחצי «סימולציית מצב» להגרלת תושבת ושולחן.';
  static const String howToStep2 =
      '2. הפעילי «ריצוי ראשון» אם זה התור הראשון שלך (30+ נקודות).';
  static const String howToStep3 = '3. לחצי «הצג מהלכים אופטימליים» לראות את כל המהלכים הטובים ביותר.';
  static const String howToStep4 =
      '4. בכל מהלך מוצגים צעדים, לפני ואחרי — כולל פירוק ובנייה מחדש של סטים.';

  static String moveStepPlayFromRack(String tiles) =>
      'הניחי מהתושבת על השולחן: $tiles';

  static String moveStepReorganizeTable(int meldsBefore, int meldsAfter) =>
      'סידור מחדש של השולחן: מ-$meldsBefore ל-$meldsAfter סטים חוקיים';
}
