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
        "Open Settings once: Series Preset, Channel Prefix, Brand & Thumbnails, and OpenAI key if you use cloud AI.",
        "Go to Smart Analysis → Scan Folder (sort the shoot — not the upload package yet).",
        "Review KEEP, B-ROLL, REVIEW, and DISCARD. Optional AI Assist / cut hints run if enabled in Settings.",
        "Optional: edit the pink Hook column for shoot-day labels, or Generate Thumbnails as a quick preview.",
        "Click Run Pipeline to move junk and send KEEP clips to Clip Cleaner.",
        "In Clip Cleaner, confirm trim/Production Pass settings and let KEEP clips polish into Processed/.",
        "Import the _CLEANED files into Filmora and finish the creative edit.",
        "Go to YouTube Prep (upload stage): choose the finished Filmora export → Transcribe & Analyze Story → Confirm Story.",
        "In YouTube Prep, pick a title, Rank Thumbnails, Generate Description/Tags, then Build Upload Package.",
        "Optional: Shorts tab — same finished video → export 1 to 2 vertical Shorts."
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
            body: "Run Smart Analysis before cleaning so obvious junk goes to _DISCARD, B-roll is labeled separately, and sudden camera jerks are flagged for review."
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
            body: "Sort the shoot folder: talking/motion/jerk scoring, KEEP / B-ROLL / REVIEW / DISCARD, optional AI Assist + cut hints, then Run Pipeline. Shoot-day hooks/thumbs here are previews — the real upload pack is YouTube Prep."
        ),
        ManualSection(
            icon: "rectangle.portrait.on.rectangle.portrait",
            title: "Shorts",
            body: "Transcribe a finished video, then get ranked Shorts with a spoken hook, projected hook/retention scores, and a best title for each moment."
        ),
        ManualSection(
            icon: "square.and.arrow.up",
            title: "YouTube Prep",
            body: "Upload stage for your finished Filmora export: Story Review, titles, Rank Thumbnails, description/tags, captions, and Build Upload Package."
        ),
        ManualSection(
            icon: "gearshape",
            title: "Settings",
            body: "One place for analysis thresholds, brand/thumbnail look (including emoticons), and OpenAI toggles."
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
            version: "1.51",
            highlights: [
                "Cleanup: removed duplicate Settings sheet on Smart Analysis, duplicate Rank Thumbnails button, and the second emoticon picker on YouTube Prep (edit brand in Settings only).",
                "Guide/README clarify shoot-day Smart Analysis vs upload-stage YouTube Prep; legacy Update And Open.command now runs the same Update.command flow."
            ]
        ),
        ManualChangelogEntry(
            version: "1.50",
            highlights: [
                "Smart Analysis cut hints (optional, Settings → OpenAI): for KEEP / REVIEW / B-ROLL clips, Whisper + GPT suggest KEEP/CUT time ranges shown in the Cut hints column and CSV. Suggestions only — Clip Cleaner does not auto-cut."
            ]
        ),
        ManualChangelogEntry(
            version: "1.49",
            highlights: [
                "Smart Analysis AI Assist (optional, Settings → OpenAI): after local KEEP/B-ROLL/REVIEW rules, OpenAI can demote obvious junk or confirm a label. It never upgrades weak clips to KEEP. Clip Cleaner / auto-editor unchanged."
            ]
        ),
        ManualChangelogEntry(
            version: "1.48",
            highlights: [
                "OpenAI API key no longer uses macOS Keychain (that password dialog often blocked Desktop Update installs). Keys are stored in a locked local app file instead — click Deny on any leftover Keychain prompt, then paste your sk- key again and Save."
            ]
        ),
        ManualChangelogEntry(
            version: "1.47",
            highlights: [
                "Thumbnails get a local punch-up (contrast/saturation/sharpen), tighter crop, and a lighter bottom fade so the picture pops more.",
                "OpenAI Vision can rerank Rank Thumbnails picks and suggest overlay text that matches what’s actually in the frame (Settings toggle).",
                "Winner frames decode at 1920 before branding for a sharper 1280×720 JPEG."
            ]
        ),
        ManualChangelogEntry(
            version: "1.46",
            highlights: [
                "Thumbnail outline is now a thick black outer ring plus a thick white inner ring around your fill color — much heavier YouTube-style pop."
            ]
        ),
        ManualChangelogEntry(
            version: "1.45",
            highlights: [
                "Thumbnail Settings stick again: YouTube Prep no longer overrides your fill color for travel/story videos.",
                "Black + red text outline is back (toggle in Settings), drawn with offset rings so letter corners don’t spike.",
                "New Thumbnail Font picker (Impact, Arial Black, Avenir Heavy, Futura, Helvetica, Georgia, System Bold)."
            ]
        ),
        ManualChangelogEntry(
            version: "1.44",
            highlights: [
                "OpenAI integration: save an API key in Settings and Hughes Clip Prep can use Whisper for transcripts plus GPT for Story Review and YouTube descriptions — one place, stronger copy.",
                "Toggles for Whisper / cloud story / cloud description with automatic fallback to Apple tools if a request fails.",
                "API key is stored in the Mac Keychain; possessive debris like “and 's …” is scrubbed from story fields."
            ]
        ),
        ManualChangelogEntry(
            version: "1.43",
            highlights: [
                "YouTube descriptions are built from confirmed Story Review fields in plain English — no more mid-sentence stubs like “and experienced delayed flights…”.",
                "Generic place lists (Office/Airport/Hotel) are de-emphasized when specific places exist; empty chapter stubs are omitted.",
                "New Copy ChatGPT Pack button pastes confirmed facts + transcript for a stronger cloud rewrite without inventing cast."
            ]
        ),
        ManualChangelogEntry(
            version: "1.42",
            highlights: [
                "Cast rules: people mentioned as at home / not coming / seen later are stripped from traveler summaries — no more Warren & Tina on a coworker trip.",
                "Channel Context spelling corrections now fix ASR aliases in the transcript and story fields (Brian → Brianna, Gabby → Gabie) when those names are listed in Settings.",
                "Story prompts prefer coworker/on-trip cues over host-couple assumptions from Channel Context."
            ]
        ),
        ManualChangelogEntry(
            version: "1.41",
            highlights: [
                "View Full Transcript in Story Review is a real toggle button now — the old disclosure control often did nothing when clicked inside the scrolling page."
            ]
        ),
        ManualChangelogEntry(
            version: "1.40",
            highlights: [
                "Invent-nothing Story Review: unsupported people, places, summaries, titles, tags, and hashtags are cleared in code when they are not grounded in the transcript.",
                "Tags/hashtags are rebuilt from spoken phrases — #FamilyTravel / #FamilyVlog cannot appear unless the transcript earns them.",
                "Unclassified videos no longer default to a Family domain (that was inventing lifestyle packaging).",
                "Channel Context default text is identity/spelling only and must not supply plot, cast, or trip themes."
            ]
        ),
        ManualChangelogEntry(
            version: "1.39",
            highlights: [
                "Apple Intelligence evidence is now checked against the literal transcript; invented quotes/speaker labels are removed and confidence is capped.",
                "Settings now stores private on-device Channel Context for correct names and pet roles (Coco is a dog; Brianna is a coworker) without assuming who traveled.",
                "Story prompts explicitly separate travelers from family/pets mentioned as support, and use channel context only for identity/spelling.",
                "Fake compressed chapter timelines are rejected instead of turning an 11-minute video into 0:00–1:20 chapters."
            ]
        ),
        ManualChangelogEntry(
            version: "1.38",
            highlights: [
                "Apple Intelligence now analyzes each transcript entirely on-device into subject, goal, obstacle, origin, problem location, destination, outcome, evidence, and confidence.",
                "A new editable Story Review must be confirmed before titles, descriptions, tags, chapters, or thumbnails can be generated.",
                "Metadata consumes only the confirmed story; preset clickbait templates and unsupported location relationships no longer drive YouTube Prep.",
                "Thumbnail ranking scans about 60 frames, puts story matches first, preserves sharp alternatives, removes conflicting food/beverage frames for travel stories, and avoids duplicate moments."
            ]
        ),
        ManualChangelogEntry(
            version: "1.37",
            highlights: [
                "A new transcript now replaces stale thumbnail text with the story phrase (for example DFW GROUND DELAYS), instead of preserving AMERICAN AIRLINES from an old run.",
                "Story matching no longer pads eight slots with irrelevant food/soda frames; blurry frames and face-filling close-ups are rejected more aggressively.",
                "Thumbnail text uses a clean shadow instead of stroked outlines, removing the pointed letter spikes; colors now follow the detected story.",
                "Travel descriptions are shorter and natural, with no repeated STORY BEATS list and better missed-business-trip phrasing."
            ]
        ),
        ManualChangelogEntry(
            version: "1.36",
            highlights: [
                "YouTube Prep is story-first: transcript builds a story brief (travel delay, cooking, F1, adventure, etc.) that drives description, tags, hashtags, and chapters.",
                "Series/playlist and Halloween emoji only appear when they fit *this* story — leftover Halloween Hunt no longer pollutes delay vlogs.",
                "Thumbnails rank by story visuals (plane/gate/OCR) with hard rejects for blur and face-filling close-ups; title outline is thinner (no spike letters)."
            ]
        ),
        ManualChangelogEntry(
            version: "1.35",
            highlights: [
                "YouTube Prep descriptions follow the real story for travel/delay videos instead of fake “walkthrough / what we found” store copy.",
                "Drops junk topics like “flight flights”, prefers delay/airport chapter titles, and builds real tags/hashtags (#flightdelay, DFW, etc.).",
                "Thumbnail ranking skips much more of the intro/outro so house outros and end cards stop winning.",
                "Auto hook suggests delay/missed-trip phrasing from the transcript instead of the first eight mumbled words."
            ]
        ),
        ManualChangelogEntry(
            version: "1.34",
            highlights: [
                "Smart Analysis now labels silent, moving clips as B-ROLL (blue) instead of dumping them into REVIEW.",
                "Pipeline leaves B-ROLL in place with KEEP cleaned and DISCARD moved — summary counts show B-ROLL separately.",
                "CSV report and thumbnails include B-ROLL clips; Settings slider renamed to “B-roll motion % for B-ROLL”."
            ]
        ),
        ManualChangelogEntry(
            version: "1.33",
            highlights: [
                "Update dialog now reads the real app version from the build (no more stale “Version 1.31” popup after installing newer code).",
                "Same AAC 48 kHz / native encoder fix as 1.32 — re-run Update once so the dialog and Clip Cleaner both show 1.33."
            ]
        ),
        ManualChangelogEntry(
            version: "1.32",
            highlights: [
                "Clip Cleaner now forces 48 kHz audio so DJI clips (often 96 kHz) stop failing with “AAC encoder only supports these samplerates…”.",
                "Also forces the native AAC encoder (not macOS aac_at) for the same DJI sample-rate cases.",
                "Production Pass and Shorts export also resample AAC to 48 kHz for the same reason."
            ]
        ),
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
