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
        "Open Hughes Clip Prep and go to Smart Analysis.",
        "Click Scan Folder and choose that folder.",
        "Wait for analysis to finish. Review KEEP, REVIEW, and DISCARD.",
        "Check the pink Title column for each clip. Click any title to edit it before generating thumbnails.",
        "Open Settings and pick a Series Preset (Halloween Hunt, Store Walk, Product Review) for consistent naming.",
        "Set your Channel Prefix and Title Format once — every clip follows the same pattern.",
        "Use Refresh Titles after changing brand settings to update every clip at once.",
        "Click Generate Thumbnails to create 1280×720 images with pink titles in Thumbnails/.",
        "Click Run Pipeline to move junk and process the keepers.",
        "Open the Processed folder and import the _CLEANED files into Filmora.",
        "Finish your creative edit in Filmora — titles, music, pacing, and final polish."
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
            icon: "camera.metering.center.weighted",
            title: "Stabilization",
            body: "Turn this ON for walking footage or clips flagged for sudden camera movement. It smooths shaky motion after trimming."
        ),
        ManualSection(
            icon: "photo.on.rectangle.angled",
            title: "Brand & Thumbnails",
            body: "Pick a series preset, set your channel prefix, and choose a title format. Hughes Clip Prep suggests titles and exports branded thumbnails with pink titles for YouTube."
        ),
        ManualSection(
            icon: "folder.badge.gearshape",
            title: "Smart Analysis First",
            body: "Run Smart Analysis before cleaning so obvious junk goes to _DISCARD and sudden camera jerks are flagged for review."
        )
    ]

    static let tabGuide: [ManualSection] = [
        ManualSection(
            icon: "scissors",
            title: "Clip Cleaner",
            body: "Batch-trim and polish clips. Choose your folder, confirm settings, and start processing. Clean files land in Processed/."
        ),
        ManualSection(
            icon: "waveform.badge.magnifyingglass",
            title: "Smart Analysis",
            body: "Scan a folder, score clips for talking and motion, detect sudden camera movement, and get KEEP / REVIEW / DISCARD recommendations."
        ),
        ManualSection(
            icon: "gearshape",
            title: "Settings",
            body: "Tune Smart Analysis thresholds for your shooting style."
        ),
        ManualSection(
            icon: "book",
            title: "Guide",
            body: "This workflow manual. It updates every time Hughes Clip Prep gets a meaningful new feature."
        )
    ]

    static let requirements: [String] = [
        "Auto-Editor — brew install auto-editor",
        "FFmpeg — brew install ffmpeg (Production Pass and stabilization)",
        "Filmora for final creative editing"
    ]

    static let changelog: [ManualChangelogEntry] = [
        ManualChangelogEntry(
            version: "1.10",
            highlights: [
                "Thumbnail titles now use a white outer outline, black inner outline, and pink fill."
            ]
        ),
        ManualChangelogEntry(
            version: "1.9",
            highlights: [
                "Thumbnail titles now have a bold black outline so pink text pops on busy frames.",
                "Settings preview matches the outlined thumbnail look."
            ]
        ),
        ManualChangelogEntry(
            version: "1.8",
            highlights: [
                "Series presets for Halloween Hunt, Store Walk, Product Review, and Behind the Scenes.",
                "Title format picker keeps every clip on the same Channel · Series · Hook pattern.",
                "Editable titles in Smart Analysis plus Refresh Titles after brand changes.",
                "Live thumbnail preview in Brand & Thumbnails settings."
            ]
        ),
        ManualChangelogEntry(
            version: "1.7",
            highlights: [
                "Suggested titles for each clip based on your brand, folder, and clip type.",
                "Generate Thumbnails creates 1280×720 images with pink branded titles.",
                "Brand & Thumbnails settings for channel prefix and series name."
            ]
        ),
        ManualChangelogEntry(
            version: "1.6",
            highlights: [
                "Renamed to Hughes Clip Prep with a professional workflow-focused design.",
                "Sudden camera movement detection flags clips for REVIEW with timestamps.",
                "Optional stabilization pass in Clip Cleaner for shaky footage."
            ]
        ),
        ManualChangelogEntry(
            version: "1.5",
            highlights: [
                "Added in-app workflow guide and changelog.",
                "Professional orange and blue interface theme."
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
                "Smart Analysis, Run Pipeline, Clip Cleaner, and Settings launched."
            ]
        )
    ]
}
