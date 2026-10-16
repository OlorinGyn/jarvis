"""Which notifications reach the phone: the cases, the three modes, and their switches.

A mode only decides what is sent; recording never changes. Each mode holds
one switch per case, all editable. The defaults are built from the older
notify_labels, so a config.json written before the modes keeps sending what
it sent; a case added later starts at its own default. See docs/HISTORY.md
section 8, backlogs 25 and 30.
"""

PERSON_CASES = ("resident_person", "probable_resident_person", "known_person", "unknown_face",
                "faceless_person")
ANIMAL_CASES = ("resident_dog", "probable_resident_dog", "other_dog", "other_animal")
CAMERA_CASES = ("camera_down",)
PROBABLE_RESIDENT_CASES = ("probable_resident_person", "probable_resident_dog")
CASES = PERSON_CASES + ANIMAL_CASES + CAMERA_CASES
MODES = ("home", "away", "silent")
DEFAULT_MODE = "away"

CASE_NAMES = {
    "resident_person": "Resident person recognised",
    "probable_resident_person": "Resident person, probable match",
    "known_person": "Other known person, or \"probably\" someone else",
    "unknown_face": "Unknown face",
    "faceless_person": "Person with no recognisable face",
    "resident_dog": "Resident dog",
    "probable_resident_dog": "Resident dog, probable match",
    "other_dog": "Other dog (another name, probably another, unidentified)",
    "other_animal": "Other animals",
    "camera_down": "Camera with no picture, and its return",
}
MODE_NAMES = {"home": "Home", "away": "Away", "silent": "Silent"}


def defaults(labels=None):
    """Every mode's switches as the user starts with them, from the older notify_labels."""
    labels = labels or ["person"]
    dogs = "dog" in labels
    animals = {"resident_dog": dogs, "probable_resident_dog": dogs, "other_dog": dogs,
               "other_animal": any(label not in ("person", "dog") for label in labels)}
    away = {**{case: True for case in PERSON_CASES}, **animals, "camera_down": True}
    home = {**away, "resident_person": False, "resident_dog": False,
            **{case: False for case in PROBABLE_RESIDENT_CASES}}
    return {"home": home, "away": away, "silent": {case: False for case in CASES}}


def normalised(stored, labels=None):
    """Stored switches made whole: every mode and case present, each a bool, anything unknown dropped."""
    result = defaults(labels)
    if not isinstance(stored, dict):
        return result
    for mode, switches in result.items():
        given = stored.get(mode)
        if not isinstance(given, dict):
            continue
        for case in CASES:
            if isinstance(given.get(case), bool):
                switches[case] = given[case]
    return result


def mode_of(settings):
    """The active mode, or the default when the stored one is unknown."""
    mode = settings.get("notify_mode")
    return mode if mode in MODES else DEFAULT_MODE


def active(settings):
    """The switches of the active mode."""
    return normalised(settings.get("notify_modes"), settings.get("notify_labels"))[mode_of(settings)]


def allowed(case, settings):
    """Whether the active mode sends this case to the phone."""
    return active(settings).get(case, False)


def holds_person(settings):
    """Whether a person's message must wait for the face scan: some person case is off.

    A person is named only after the clip is scanned, so a mode that leaves
    anyone out cannot decide before then.
    """
    switches = active(settings)
    return not all(switches[case] for case in PERSON_CASES)


def describe(mode, settings):
    """One line saying what a mode sends, for a Telegram answer."""
    switches = normalised(settings.get("notify_modes"), settings.get("notify_labels"))[mode]
    on = [CASE_NAMES[case] for case in CASES if switches[case]]
    if not on:
        return f"{MODE_NAMES[mode]}: nothing is sent."
    return f"{MODE_NAMES[mode]}: sends {'; '.join(on)}."
