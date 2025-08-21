
// Custom Action: DeviceCalendar_CreateEvent
// Requires pubspec dep: device_calendar: ^4.3.1 (add in Flutter project settings)
// iOS: add NSCalendarsUsageDescription in Info.plist
import 'package:flutter/foundation.dart';
import 'package:device_calendar/device_calendar.dart';

final DeviceCalendarPlugin _deviceCalendarPlugin = DeviceCalendarPlugin();

/// Creates a calendar event on the specified calendarId.
/// Returns the created eventId or throws on error.
Future<String?> deviceCalendarCreateEvent({
  required String calendarId,
  required String title,
  required DateTime start,
  required DateTime end,
  bool allDay = false,
  String? location,
  String? notes,
  String? rrule, // e.g., "FREQ=WEEKLY;BYDAY=MO,WE,FR"
}) async {
  // Request permissions if needed
  var permissionsGranted = await _deviceCalendarPlugin.hasPermissions();
  if (permissionsGranted.isSuccess && !(permissionsGranted.data ?? false)) {
    final permResult = await _deviceCalendarPlugin.requestPermissions();
    if (!(permResult.isSuccess && (permResult.data ?? false))) {
      throw Exception('Calendar permission denied');
    }
  }

  final event = Event(calendarId,
      title: title,
      start: start,
      end: end,
      allDay: allDay,
      location: location,
      description: notes);

  if (rrule != null && rrule.isNotEmpty) {
    event.recurrenceRule = RecurrenceRule(RecurrenceFrequency.Weekly);
    // NOTE: device_calendar has limited RRULE support; map your needs here.
  }

  final createResult = await _deviceCalendarPlugin.createOrUpdateEvent(event);
  if (!(createResult.isSuccess)) {
    throw Exception('Failed to create event: ${createResult.errors}');
  }
  return createResult.data;
}
