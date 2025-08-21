
// Custom Function: scoreConfidence
// Simple heuristic confidence score (0-1).
double scoreConfidence({
  required bool hasDate,
  required bool hasTime,
  required bool hasLabel,
}) {
  double c = 0.6;
  if (hasDate) c += 0.2;
  if (hasTime) c += 0.1;
  if (hasLabel) c += 0.1;
  return c.clamp(0.0, 1.0);
}
