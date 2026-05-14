"""
All user-facing strings in one place.
To change the language, edit the values in class S.
"""


class S:

    # ── Allgemeine Fehler ────────────────────────────────────────────────────
    NO_PERMISSION_GUILD     = "Du benötigst die Berechtigung 'Server verwalten'."
    NO_ACCESS               = "Kein Zugriff."
    ALREADY_DONE            = "Dieser Termin ist bereits abgeschlossen."

    # ── Admin: Panel ─────────────────────────────────────────────────────────
    PANEL_CREATED           = "Panel **{name}** in {channel} erstellt.\nFüge Buttons hinzu mit `/timely add_type panel:{name} label:...`"
    PANEL_ALREADY_EXISTS    = "Ein Panel mit dem Namen **{name}** existiert bereits."
    PANEL_NOT_FOUND         = "Panel **{name}** nicht gefunden."
    PANEL_NO_CHANNEL        = "Panel **{name}** hat keinen Channel."
    PANEL_DELETED           = "Panel **{name}** und alle zugehörigen Buttons wurden gelöscht."
    PANEL_POSTED            = "Panel **{name}** gepostet."
    PANEL_REFRESHED         = "Panel **{name}** aktualisiert."
    PANEL_NO_TYPES          = "Panel **{name}** hat keine Buttons. Füge welche hinzu mit `/timely add_type`."
    NO_PANELS               = "Keine Panels konfiguriert."
    PANELS_TITLE            = "Konfigurierte Panels"

    # ── Admin: Termintyp ─────────────────────────────────────────────────────
    TYPE_ADDED              = "Button **{label}** zu Panel **{panel}** hinzugefügt."
    TYPE_ADDED_CREATOR_ROLE = "Ersteller-Rolle: {role}"
    TYPE_ADDED_INVITEE_ROLE = "Einladbare Rolle: {role}"
    TYPE_NOT_FOUND          = "Kein Button **{label}** in Panel **{panel}** gefunden."
    TYPE_REMOVED            = "Button **{label}** aus Panel **{panel}** entfernt. Nutze `/timely refresh_panel panel:{panel}` um das Panel zu aktualisieren."
    NO_TYPES                = "Panel **{panel}** hat noch keine Buttons."
    TYPES_TITLE             = "Buttons in Panel '{panel}'"
    TYPE_CREATOR_ROLE       = "Button nutzbar für"
    TYPE_INVITEE_ROLE       = "Einladbar"
    ROLE_ALL                = "Alle"
    PANEL_NOT_FOUND_USE_CREATE = "Panel **{panel}** nicht gefunden. Erstelle es zuerst mit `/timely create_panel`."

    # ── Panel-View (öffentlich) ───────────────────────────────────────────────
    PANEL_EMBED_TITLE       = "Termin anfragen — {panel_name}"
    PANEL_EMBED_DESC        = "Wähle einen Termintyp, um eine neue Terminanfrage zu stellen."
    TYPE_GONE               = "Dieser Termintyp existiert nicht mehr."
    NO_PERMISSION_TYPE      = "Du hast keine Berechtigung, diesen Termintyp zu nutzen."
    NO_ELIGIBLE_MEMBERS     = "Keine einladbaren Nutzer mit der erforderlichen Rolle gefunden."

    # ── Schritt 1: Teilnehmer ─────────────────────────────────────────────────
    STEP1_HEADER            = "Schritt 1/3 — Wähle die Teilnehmer für deine Terminanfrage:"
    SELECT_PARTICIPANTS     = "Teilnehmer auswählen..."
    MIN_ONE_PARTICIPANT     = "Bitte mindestens einen Teilnehmer auswählen."
    CREATOR_SELF_SELECT     = "Du kannst dich nicht selbst als Teilnehmer auswählen."
    CREATOR_AUTO_REMOVED    = "Du wurdest als Ersteller automatisch aus den Teilnehmern entfernt."
    PROCEED_BUTTON          = "Weiter →"

    # ── Schritt 2: Slot-Picker ────────────────────────────────────────────────
    STEP2_HEADER            = "**Schritt 2/3 — Zeitvorschläge**"
    STEP2_INSTRUCTION       = "Wähle Datum, Stunde und Minute, dann klicke **+ Slot hinzufügen**."
    SLOTS_ADDED_LABEL       = "**Hinzugefügte Slots:**"
    SLOT_DUPLICATE          = "Dieser Slot wurde bereits hinzugefügt."
    DATE_PLACEHOLDER        = "Datum wählen"
    HOUR_PLACEHOLDER        = "Stunde wählen"
    MINUTE_PLACEHOLDER      = "Minute wählen"
    ADD_SLOT_BUTTON         = "+ Slot hinzufügen"
    REMOVE_LAST_BUTTON      = "Letzten entfernen"

    # ── Schritt 3: Modal ─────────────────────────────────────────────────────
    MODAL_TITLE             = "Schritt 3/3 — Termin Details"
    MODAL_FIELD_TITLE       = "Titel"
    MODAL_FIELD_TITLE_PH    = "z.B. Team-Meeting Q2"
    MODAL_FIELD_DESC        = "Beschreibung"
    MODAL_FIELD_DESC_PH     = "Worum geht es?"
    EVENT_CREATED           = "Terminanfrage **{title}** erstellt! Einladungen wurden an {count} Teilnehmer versendet.\nDu erhältst die Status-Übersicht per DM."
    EVENT_CREATED_DM_FAILED = "\nFolgende Nutzer konnten nicht per DM erreicht werden: {names}"

    # ── Vote-View (Teilnehmer-DM) ─────────────────────────────────────────────
    VOTE_EMBED_TITLE        = "Termineinladung: {title}"
    VOTE_FIELD_CREATOR      = "Erstellt von"
    VOTE_FIELD_DESC         = "Beschreibung"
    VOTE_FIELD_SLOTS        = "Zeitvorschläge"
    VOTE_FOOTER             = "Bitte wähle alle Zeitfenster, die für dich passen. Diese Anfrage läuft in 7 Tagen ab."
    VOTE_SELECT_PH          = "Wähle alle passenden Zeitfenster..."
    VOTE_DECLINE_BUTTON     = "Ablehnen"
    VOTE_SAVED              = "Deine Verfügbarkeit wurde gespeichert. Danke!"
    VOTE_DECLINED           = "Du hast den Termin abgelehnt."

    # ── Creator-DM (Status-View) ──────────────────────────────────────────────
    CREATOR_INITIAL_TITLE   = "📅 Termin erstellt: {title}"
    CREATOR_INITIAL_SLOTS   = "Zeitvorschläge"
    CREATOR_INITIAL_MEMBERS = "Eingeladene Teilnehmer"
    CREATOR_INITIAL_FOOTER  = "Sobald alle geantwortet haben wird der beste Slot automatisch gewählt. Du kannst den Termin auch jederzeit manuell bestätigen."
    CREATOR_AUTO_AVAILABLE  = "✅ Du (automatisch für alle Slots verfügbar)"

    CREATOR_STATUS_TITLE    = "📅 {title}"
    CREATOR_STATUS_CONFIRMED= "✅ Bestätigt"
    CREATOR_STATUS_OPEN     = "🔄 Offen"
    CREATOR_FIELD_STATUS    = "Status"
    CREATOR_FIELD_ANSWERS   = "Antworten"
    CREATOR_FIELD_PENDING   = "Ausstehend"
    CREATOR_FIELD_SLOTS     = "Zeitvorschläge"
    CREATOR_SLOT_CONFIRMED  = " ← bestätigt"
    CREATOR_FIELD_MEMBERS   = "Teilnehmer"
    CREATOR_CANCEL_BUTTON   = "Terminanfrage abbrechen"

    # ── Abbruch ───────────────────────────────────────────────────────────────
    CANCEL_EMBED_TITLE      = "❌ Termin abgesagt: {title}"
    CANCEL_EMBED_DESC       = "Die Terminanfrage wurde vom Ersteller abgesagt."
    CANCEL_CONFIRMED        = "Termin **{title}** wurde abgesagt. Alle Teilnehmer wurden informiert."

    # ── Bestätigung ───────────────────────────────────────────────────────────
    CONFIRM_EMBED_TITLE     = "📅 Termin bestätigt: {title}"
    CONFIRM_EMBED_DESC      = "Der finale Termin steht fest:\n**{time}**"
    CONFIRM_FOOTER          = "Die .ics Datei im Anhang kannst du direkt in deinen Kalender importieren."
    CONFIRM_NO_PERFECT_SLOT = "Kein Slot passte allen — gewählt wurde der Slot mit der höchsten Verfügbarkeit ({count}/{total})."
    CONFIRM_FIELD_HINT      = "Hinweis"
    CONFIRM_SUCCESS         = "Termin **{title}** auf **{time}** bestätigt. Alle wurden informiert."
    CONFIRM_DM_FAILED       = "\nFolgende Nutzer konnten nicht per DM erreicht werden: {ids}"

    # ── /timely status ────────────────────────────────────────────────────────
    STATUS_NO_OPEN_EVENTS   = "Du hast keine offenen Termine."
    STATUS_PICK_EVENT       = "Du hast mehrere offene Termine. Wähle einen aus:"
    STATUS_PICK_PH          = "Termin auswählen..."

    # ── /timely remind ────────────────────────────────────────────────────────
    REMIND_ALL_ANSWERED     = "Alle Teilnehmer haben bereits geantwortet."
    REMIND_SENT             = "Erinnerung an **{count}** Teilnehmer gesendet."
    REMIND_FAILED           = "\nFolgende Nutzer konnten nicht erreicht werden: {ids}"
    REMIND_PREFIX           = "Erinnerung: Du hast noch nicht auf diese Terminanfrage geantwortet."
    REMIND_PICK_EVENT       = "Du hast mehrere offene Termine. Wähle einen aus:"
