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
        "Check the pink Hook column for each clip. Click to type your own hook before generating thumbnails.",
        "Full Title updates automatically from Channel · Series · Hook.",
        "Open Settings and pick a Series Preset (Halloween Hunt, Store Walk, Product Review) for consistent naming.",
        "Set your Channel Prefix and Title Format once — every clip follows the same pattern.",
        "Use Refresh Titles after changing brand settings to update every clip at once.",
        "Click Generate Thumbnails to create 1280×720 images with pink titles in Thumbnails/.",
        "Click Run Pipeline to move junk and process the keepers.",
        "Open the Processed folder and import the _CLEANED files into Filmora.",
        "Finish your creative edit in Filmora — titles, music, pacing, and final polish.",
        "Go to YouTube Prep, choose your finished export, type your hook, and build the upload package.",
        "Open the Shorts tab, point at the same finished video, and export 1 to 2 vertical Shorts from it."
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
            icon: "rectangle.portrait.on.rectangle.portrait",
            title: "Shorts",
            body: "Transcribe a finished video, then get ranked Shorts with a spoken hook, projected hook/retention scores, and a best title for each moment."
        ),
        ManualSection(
            icon: "square.and.arrow.up",
            title: "YouTube Prep",
            body: "Transcribe your finished Filmora export, pick from ten CTR-ranked titles, rank about 30 thumbnail frames, then build the upload package."
        ),
        ManualSection(
            icon: "gearshape",
            title: "Settings",
            body: "Tune Smart Analysis thresholds and your brand style for titles and thumbnails."
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
            version: "1.31",
            highlights: [
                "Shorts are rebuilt as story splices: HOOK + PAYOFF + BUTTON cut from different timestamps, not one continuous 30s slice.",
                "Titles cleaned from the payoff find instead of dumping raw transcript junk.",
                "UI and upload notes list each cut so you can see the mini-edit before you export."
            ]
        ),
        ManualChangelogEntry(
            version: "1.30",
            highlights: [
                "Each Short now comes with a creative brief: story beats (hook / build / button), music mood + search terms, mix tip, and Filmora/CapCut framing ideas.",
                "Briefs also land in Shorts_upload_notes.txt after export so you can edit with a recipe, not just a raw clip.",
                "Default Short length is back to 30 seconds."
            ]
        ),
        ManualChangelogEntry(
            version: "1.29",
            highlights: [
                "Shorts length choices now go to 60s and 90s (default 60s) — not stuck at a 30-second tease.",
                "Clearer Shorts tab copy: each export is one vertical moment from your long video, uploaded separately."
            ]
        ),
        ManualChangelogEntry(
            version: "1.28",
            highlights: [
                "Shorts export no longer fails when FFmpeg is missing text filters (ass / drawtext).",
                "If captions cannot be burned in, the vertical MP4 still exports and a matching .srt is saved beside it.",
                "Status tip explains how to reinstall a full FFmpeg for burned-in captions."
            ]
        ),
        ManualChangelogEntry(
            version: "1.27",
            highlights: [
                "Shorts captions now burn with FFmpeg drawtext — works even when your FFmpeg was built without libass.",
                "Fixes “No such filter: ass” on Export Selected Shorts."
            ]
        ),
        ManualChangelogEntry(
            version: "1.26",
            highlights: [
                "Fixed Shorts export failing with FFmpeg exit code 234 when burning captions.",
                "Caption filter now uses filename= path syntax that newer FFmpeg accepts.",
                "Shorts file names strip spaces and “(copy)” so exports land cleanly in Finder."
            ]
        ),
        ManualChangelogEntry(
            version: "1.25",
            highlights: [
                "Pick Your Thumbnail Picture sits directly above Generate — no more hunting past the title list.",
                "Orange Rank Thumbnails button also appears in the Generate row next to Quick Thumbnail.",
                "Clear callout explains: rank frames, then click a picture to select it."
            ]
        ),
        ManualChangelogEntry(
            version: "1.24",
            highlights: [
                "Fixed the Xcode Release build that was failing after Update on newer macOS toolchains.",
                "Thumbnail ranking progress updates stay on the main thread so Rank Thumbnails compiles cleanly.",
                "Frame capture uses the current AVFoundation async API instead of the deprecated copy path."
            ]
        ),
        ManualChangelogEntry(
            version: "1.23",
            highlights: [
                "Thumbnail Picks sit right under the video fields again — no more scrolling past ten titles to find them.",
                "Rank Thumbnails now offers eight picture choices in a clickable grid, not just three.",
                "Title Choices moved into their own section below the picture picker."
            ]
        ),
        ManualChangelogEntry(
            version: "1.22",
            highlights: [
                "Stores are only recognized from a known retailer list — cities and misheard speech like \"medicine Bumgardner\" are no longer listed as stores.",
                "Chapter titles now need a two-word subject, so lone words like \"Sugar\" are skipped.",
                "WHAT WE FOUND no longer repeats the same subject or lists store names as finds."
            ]
        ),
        ManualChangelogEntry(
            version: "1.21",
            highlights: [
                "Pick up to two emoticons for thumbnails — pumpkin, ghost, bat, fire, sandwich, and more.",
                "Choose where they land: top right, top left, both top corners, or beside the title.",
                "Emoticon picker is in Settings and also on the YouTube Prep Thumbnail Picks section."
            ]
        ),
        ManualChangelogEntry(
            version: "1.20",
            highlights: [
                "Pick any thumbnail text color with a color picker, plus one-click swatches for pink, papaya, yellow, lime, cyan, and blood red.",
                "New text size slider from 60% to 160%, with a reset to 100%.",
                "The Settings preview now matches the real color and size instead of showing a fixed sample."
            ]
        ),
        ManualChangelogEntry(
            version: "1.19",
            highlights: [
                "Descriptions are written from what is in the video instead of repeating your title in every sentence.",
                "Export filenames no longer leak into titles — no more \"2026 07 29 18 59 18(copy)\".",
                "Store names are recognized and become the strongest tags, since that is what viewers search.",
                "New Stores & Places field for names the microphone missed.",
                "Repeated subjects are collapsed, so no more \"spice spice\" or three kinds of pumpkin."
            ]
        ),
        ManualChangelogEntry(
            version: "1.18",
            highlights: [
                "Fixed thumbnail picks never appearing — Finder was opening on top of the app and hiding them.",
                "Thumbnail Picks is now its own section near the top of YouTube Prep.",
                "Live progress while scanning, so a long video no longer looks frozen.",
                "Scanning is much faster: frames are scored at preview size and only the winners are rendered full quality."
            ]
        ),
        ManualChangelogEntry(
            version: "1.17",
            highlights: [
                "Fixed junk tags — \"don know\" and \"they got\" came from splitting contractions and pairing words that were never spoken together.",
                "Tags now come from real subjects in your speech, like \"halloween candles\" instead of filler.",
                "Chapters are named after what you were actually talking about, and are skipped rather than guessed at.",
                "Descriptions list what's in the video instead of dumping raw transcript text."
            ]
        ),
        ManualChangelogEntry(
            version: "1.16",
            highlights: [
                "Thumbnail Intelligence scores about 30 frames and shows Top / Second / Third picks to choose from.",
                "Shorts now feel like an assistant — spoken hook, duration, projected hook & retention, and a best title per Short.",
                "YouTube Prep generates ten CTR-ranked title options so you have real choices, not just three."
            ]
        ),
        ManualChangelogEntry(
            version: "1.15",
            highlights: [
                "On-device speech transcription for finished videos.",
                "YouTube Prep builds real chapters, spoken-word descriptions, tags, and an .srt captions file.",
                "Shorts picks moments from what you said and can burn large captions onto the vertical export."
            ]
        ),
        ManualChangelogEntry(
            version: "1.14",
            highlights: [
                "New Shorts tab finds the strongest moments in a finished video automatically.",
                "Exports vertical 1080x1920 clips at 20, 30, or 45 seconds with Shorts loudness.",
                "Writes a notes file with titles, descriptions, and the steps that turn Shorts viewers into subscribers."
            ]
        ),
        ManualChangelogEntry(
            version: "1.13",
            highlights: [
                "YouTube titles now lead with your hook instead of your channel name, which is what search ranks on.",
                "Separate short thumbnail text so the image stays readable on a phone.",
                "Descriptions front-load a 150-character search snippet and include chapters.",
                "Tags are keyword-first, multi-word, and capped to YouTube's 500-character budget.",
                "Live quality checks warn when a title, thumbnail, or tag set will hurt reach."
            ]
        ),
        ManualChangelogEntry(
            version: "1.12",
            highlights: [
                "New YouTube Prep tab for finished Filmora exports.",
                "Generate thumbnail, description, and tags from one video file.",
                "Build Upload Package saves title, description, tags, and thumbnail into YouTube_Prep/."
            ]
        ),
        ManualChangelogEntry(
            version: "1.11",
            highlights: [
                "Editable Hook column in Smart Analysis — type just the hook, full title builds automatically.",
                "Default Hook field in Settings for thumbnail preview."
            ]
        ),
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
