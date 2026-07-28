import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            CleanerView()
                .tabItem {
                    Label("Clip Cleaner", systemImage: "sparkles")
                }

            AnalysisView()
                .tabItem {
                    Label("Smart Analysis", systemImage: "waveform.badge.magnifyingglass")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
        .frame(
            minWidth: 900,
            idealWidth: 1_000,
            minHeight: 720,
            idealHeight: 800
        )
    }
}

#Preview {
    MainTabView()
}
