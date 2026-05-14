"""
All user-facing strings in one place.
To change the language, edit the values in class S.
"""


class S:

    # ── General errors ───────────────────────────────────────────────────────
    NO_PERMISSION_GUILD     = 'You need the "Manage Server" permission.'
    NO_ACCESS               = "No access."
    ALREADY_DONE            = "This event has already ended."

    # ── Admin: Panel ─────────────────────────────────────────────────────────
    PANEL_CREATED           = "Panel **{name}** created in {channel}.\nAdd buttons using `/timely add_type panel:{name} label:...`"
    PANEL_ALREADY_EXISTS    = "A panel named **{name}** already exists."
    PANEL_NOT_FOUND         = "Panel **{name}** not found."
    PANEL_NO_CHANNEL        = "Panel **{name}** has no channel."
    PANEL_DELETED           = "Panel **{name}** and all associated buttons have been deleted."
    PANEL_POSTED            = "Panel **{name}** posted."
    PANEL_REFRESHED         = "Panel **{name}** updated."
    PANEL_NO_TYPES          = "Panel **{name}** has no buttons. Add some using `/timely add_type`."
    NO_PANELS               = "No panels configured."
    PANELS_TITLE            = "Configured panels"

    # ── Admin: Appointment type ───────────────────────────────────────────────
    TYPE_ADDED              = "Button **{label}** added to panel **{panel}**."
    TYPE_ADDED_CREATOR_ROLE = "Creator role: {role}"
    TYPE_ADDED_INVITEE_ROLE = "Invitable role: {role}"
    TYPE_NOT_FOUND          = "No button **{label}** found in panel **{panel}**."
    TYPE_REMOVED            = "Button **{label}** removed from panel **{panel}**. Use `/timely refresh_panel panel:{panel}` to refresh the panel."
    NO_TYPES                = "Panel **{panel}** has no buttons yet."
    TYPES_TITLE             = 'Buttons in panel "{panel}"'
    TYPE_CREATOR_ROLE       = "Button available to"
    TYPE_INVITEE_ROLE       = "Invitees"
    ROLE_ALL                = "Everyone"
    PANEL_NOT_FOUND_USE_CREATE = "Panel **{panel}** not found. Create it first using `/timely create_panel`."

    # ── Panel view (public) ───────────────────────────────────────────────────
    PANEL_EMBED_TITLE       = "Request a meeting — {panel_name}"
    PANEL_EMBED_DESC        = "Select a meeting type to create a new meeting request."
    TYPE_GONE               = "This meeting type no longer exists."
    NO_PERMISSION_TYPE      = "You do not have permission to use this appointment type."
    NO_ELIGIBLE_MEMBERS     = "No users with the required role found to invite."

    # ── Step 1: Participants ──────────────────────────────────────────────────
    STEP1_HEADER            = "Step 1/3 — Select the participants for your appointment request:"
    SELECT_PARTICIPANTS     = "Select participants..."
    MIN_ONE_PARTICIPANT     = "Please select at least one participant."
    CREATOR_SELF_SELECT     = "You cannot select yourself as a participant."
    CREATOR_AUTO_REMOVED    = "As the organiser, you have been automatically removed from the list of participants."
    PROCEED_BUTTON          = "Continue →"

    # ── Step 2: Slot picker ───────────────────────────────────────────────────
    STEP2_HEADER            = "**Step 2/3 — Suggested times**"
    STEP2_INSTRUCTION       = "Select the date, hour and minute, then click **+ Add slot**."
    SLOTS_ADDED_LABEL       = "**Slots added:**"
    SLOT_DUPLICATE          = "This slot has already been added."
    DATE_PLACEHOLDER        = "Select date"
    HOUR_PLACEHOLDER        = "Select hour"
    MINUTE_PLACEHOLDER      = "Select minute"
    ADD_SLOT_BUTTON         = "+ Add slot"
    REMOVE_LAST_BUTTON      = "Remove last"

    # ── Step 3: Modal ─────────────────────────────────────────────────────────
    MODAL_TITLE             = "Step 3/3 — Event details"
    MODAL_FIELD_TITLE       = "Title"
    MODAL_FIELD_TITLE_PH    = "e.g. Team meeting Q2"
    MODAL_FIELD_DESC        = "Description"
    MODAL_FIELD_DESC_PH     = "What is it about?"
    EVENT_CREATED           = "Event request **{title}** created! Invitations have been sent to {count} participants.\nYou will receive the status overview via DM."
    EVENT_CREATED_DM_FAILED = "\nThe following users could not be reached via DM: {names}"

    # ── Vote view (participant DM) ────────────────────────────────────────────
    VOTE_EMBED_TITLE        = "Event invitation: {title}"
    VOTE_FIELD_CREATOR      = "Created by"
    VOTE_FIELD_DESC         = "Description"
    VOTE_FIELD_SLOTS        = "Suggested times"
    VOTE_FOOTER             = "Please select all time slots that suit you. This request expires in 7 days."
    VOTE_SELECT_PH          = "Select all suitable time slots..."
    VOTE_DECLINE_BUTTON     = "Decline"
    VOTE_SAVED              = "Your availability has been saved. Thank you!"
    VOTE_DECLINED           = "You have declined the event."

    # ── Creator DM (status view) ──────────────────────────────────────────────
    CREATOR_INITIAL_TITLE   = "📅 Event created: {title}"
    CREATOR_INITIAL_SLOTS   = "Suggested times"
    CREATOR_INITIAL_MEMBERS = "Invited participants"
    CREATOR_INITIAL_FOOTER  = "Once everyone has replied, the best slot will be selected automatically. You can also confirm the event manually at any time."
    CREATOR_AUTO_AVAILABLE  = "✅ You (automatically available for all slots)"

    CREATOR_STATUS_TITLE    = "📅 {title}"
    CREATOR_STATUS_CONFIRMED= "✅ Confirmed"
    CREATOR_STATUS_OPEN     = "🔄 Open"
    CREATOR_FIELD_STATUS    = "Status"
    CREATOR_FIELD_ANSWERS   = "Replies"
    CREATOR_FIELD_PENDING   = "Pending"
    CREATOR_FIELD_SLOTS     = "Time suggestions"
    CREATOR_SLOT_CONFIRMED  = " ← confirmed"
    CREATOR_FIELD_MEMBERS   = "Participants"
    CREATOR_CANCEL_BUTTON   = "Cancel appointment request"

    # ── Cancellation ─────────────────────────────────────────────────────────
    CANCEL_EMBED_TITLE      = "❌ Appointment cancelled: {title}"
    CANCEL_EMBED_DESC       = "The appointment request has been cancelled by the organiser."
    CANCEL_CONFIRMED        = "Appointment **{title}** has been cancelled. All participants have been informed."

    # ── Confirmation ──────────────────────────────────────────────────────────
    CONFIRM_EMBED_TITLE     = "📅 Appointment confirmed: {title}"
    CONFIRM_EMBED_DESC      = "The final appointment has been set:\n**{time}**"
    CONFIRM_FOOTER          = "You can import the attached .ics file directly into your calendar."
    CONFIRM_NO_PERFECT_SLOT = "No slot suited everyone — the slot with the highest availability was chosen ({count}/{total})."
    CONFIRM_FIELD_HINT      = "Note"
    CONFIRM_SUCCESS         = "Appointment **{title}** at **{time}** confirmed. Everyone has been notified."
    CONFIRM_DM_FAILED       = "\nThe following users could not be reached via DM: {ids}"

    # ── /timely status ────────────────────────────────────────────────────────
    STATUS_NO_OPEN_EVENTS   = "You have no pending appointments."
    STATUS_PICK_EVENT       = "You have several pending appointments. Select one:"
    STATUS_PICK_PH          = "Select appointment..."

    # ── /timely remind ────────────────────────────────────────────────────────
    REMIND_ALL_ANSWERED     = "All participants have already replied."
    REMIND_SENT             = "Reminder sent to **{count}** participants."
    REMIND_FAILED           = "\nThe following users could not be reached: {ids}"
    REMIND_PREFIX           = "Reminder: You have not yet replied to this appointment request."
    REMIND_PICK_EVENT       = "You have several pending appointments. Select one:"
