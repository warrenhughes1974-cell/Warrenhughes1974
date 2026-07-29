import Foundation

struct ManualSection: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let body: String
}

struct ManualChangelogEntry: Identifiable {
    let id = UUID()
    let version: String
    let highlights: [String]
}

enum AppManual {
    static let lastUpdatedVersion = AppIdentity.version

    static let workflowSteps: [String] = [
        "Copy your DJI clips into one folder on your Mac.",
        "Open Hughes Hot Lap and go to Smart Analysis.",
        "Click the blue Scan Folder button and choose that folder.",
        "Wait for analysis to finish. Review KEEP, REVIEW, and DISCARD.",
        "Click Run Pipeline to toss junk and auto-clean the keepers.",
        "Open the Processed folder and import the _CLEANED files into Filmora.",
        "Do your creative edit in Filmora — titles, music, pacing, final polish."
    ]

    static let recommendedSettings: [ManualSection] = [
        ManualSection(
            icon: "scissors",
            title: "Trim Mode",
            body: "Use Start & End Only. This cuts dead air before you start talking and after you stop, but keeps natural pauses in the middle."
        ),
        ManualSection(
            icon: "bolt.fill",
            title: "Cutting Style",
            body: "Use Aggressive for tight edge trims on setup and teardown footage."
        ),
        ManualSection(
            icon: "waveform.badge.magnifyingglass",
            title: "Production Pass",
            body: "Leave this ON. It denoises audio, normalizes loudness, and removes awkward pauses longer than about 2 seconds."
        ),
        ManualSection(
            icon: "folder.badge.gearshape",
            title: "Smart Analysis First",
            body: "Run Smart Analysis before cleaning so obvious junk goes to _DISCARD and you do not waste time polishing clips you will never use."
        )
    ]

    static let tabGuide: [ManualSection] = [
        ManualSection(
            icon: "flag.checkered",
            title: "Pit Lane",
            body: "Batch-trim and polish clips. Choose your folder, confirm settings, and start processing. Clean files land in Processed/."
        ),
        ManualSection(
            icon: "binoculars.fill",
            title: "Scouting",
            body: "Scan a folder, score clips for talking and motion, and get KEEP / REVIEW / DISCARD recommendations."
        ),
        ManualSection(
            icon: "wrench.and.screwdriver.fill",
            title: "Garage Setup",
            body: "Tune Smart Analysis thresholds for your shooting style."
        ),
        ManualSection(
            icon: "book.fill",
            title: "Race Manual",
            body: "This guide. It updates every time Hughes Hot Lap gets a meaningful new feature."
        )
    ]

    static let requirements: [String] = [
        "Auto-Editor — brew install auto-editor",
        "FFmpeg — brew install ffmpeg (needed for Production Pass)",
        "Filmora for final creative editing"
    ]

    static let changelog: [ManualChangelogEntry] = [
        ManualChangelogEntry(
            version: "1.5",
            highlights: [
                "Rebranded to Hughes Hot Lap with McLaren F1 colors.",
                "Added Race Manual tab with workflow guide and changelog."
            ]
        ),
        ManualChangelogEntry(
            version: "1.4",
            highlights: [
                "Production Pass: denoise, loudness normalize, and long-pause cleanup.",
                "Requires FFmpeg."
            ]
        ),
        ManualChangelogEntry(
            version: "1.3",
            highlights: [
                "Start & End Only trim mode protects middle pauses.",
                "Aggressive edges without chopping every breath."
            ]
        ),
        ManualChangelogEntry(
            version: "1.2",
            highlights: [
                "Scan Folder button always available.",
                "Update.command rebuilds the Desktop app automatically."
            ]
        ),
        ManualChangelogEntry(
            version: "1.1",
            highlights: [
                "Clips sorted by DJI capture timestamp.",
                "Recorded column added to analysis and CSV export."
            ]
        ),
        ManualChangelogEntry(
            version: "1.0",
            highlights: [
                "Smart Analysis, Run Pipeline, Clip Cleaner, and Settings tabs launched."
            ]
        )
    ]
}
