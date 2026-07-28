import SwiftUI

/// Placeholder shell for your existing Clip Cleaner.
/// Your working ContentView.swift logic should move into this view (or CleanerViewModel)
/// without changing behavior.
struct CleanerView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "sparkles")
                .font(.system(size: 48))
                .foregroundStyle(.blue)

            Text("Clip Cleaner")
                .font(.largeTitle.bold())

            Text("Your existing cleaner is preserved in your Xcode project.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)

            GroupBox("Next step on your Mac") {
                VStack(alignment: .leading, spacing: 10) {
                    Text("1. In Xcode, drag all files from the `DJI_Clip_Cleaner_Pro` folder into your project.")
                    Text("2. Replace this placeholder `CleanerView.swift` with your current `ContentView.swift` body, or rename ContentView → CleanerView.")
                    Text("3. Set `MainTabView` as the app root (already wired in `DJI_Clip_Cleaner_ProApp.swift`).")
                    Text("4. Press Run — you should see both tabs: Clip Cleaner + Smart Analysis.")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .font(.callout)
            }

            Text("Once migrated, this tab keeps working exactly as before. Smart Analysis lives on its own tab.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    CleanerView()
}
