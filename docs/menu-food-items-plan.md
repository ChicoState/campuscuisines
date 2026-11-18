# Food Items and Menu Items

## Delivered scope

This feature uses two related catalog models:

- `FoodItem` is the reusable dish record. An eligible signed-in campus user can
  submit its name, description, and optional existing tags from the Menu page.
  The submitter is retained for attribution and the record is immediately
  available for staff to select.
- `MenuItem` is a scheduled publication of a `FoodItem`. Staff schedule a
  recurring weekday and a start/end time in Django admin. The public Menu page
  displays active entries only when the current time in the configured project
  timezone is within that schedule.

The access levels are `public` for reading the current menu, `authenticated`
for submitting a FoodItem, and `staff/admin` for scheduling or editing menu
entries. Server-side eligibility checks enforce the authenticated boundary.

Schedules are same-day recurring windows. End times must be later than start
times; overnight windows and one-off calendar dates are intentionally deferred.
Existing placeholder `MenuItem` name/description rows remain readable for
backward compatibility, but new scheduled entries should reference a
`FoodItem`.

## Verification

Model tests cover FoodItem attribution, menu relationships, current-time
filtering, inactive entries, and invalid time ranges. The navigation tests cover
public rendering and eligible-user FoodItem submission.
