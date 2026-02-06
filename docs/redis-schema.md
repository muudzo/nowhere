# Redis Schema (Phase-1)

Key patterns
- `nowhere:activity:{activity_id}` -> serialized Activity (TTL)
- `nowhere:activities:geo` -> GEO index mapping activity_id -> lat/lon (no TTL; cleaned when activity removed)
- `nowhere:join:{join_id}` -> serialized Join (TTL)
- `nowhere:activity_attendees:{activity_id}` -> SET of attendee_ids (TTL to match activity)
- `nowhere:message:{message_id}` -> serialized Message (TTL)
- `nowhere:activity_messages:{activity_id}` -> LIST of serialized Message objects (trim/expire by TTL)
- `nowhere:presence:{activity_id}:{attendee_id}` -> ephemeral presence key (SET with small TTL refreshed by client)

Notes
- TTLs kept conservative (e.g., 6 hours) for discovery; long-lived archives are exported to Postgres in Phase-2.
- GEO index uses `GEOADD` / `GEOSEARCH` for nearby discovery. Remove points when activity expires.
