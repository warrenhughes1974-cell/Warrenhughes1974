import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    @StateObject private var cleanerViewModel = CleanerViewModel()

    var body: some View {
        TabView(selection: $selectedTab) {
            CleanerView(viewModel: cleanerViewModel)
                .tabItem {
                    Label("Clip Cleaner", systemImage: "sparkles")
                }
                .tag(0)

            AnalysisView(
                cleanerViewModel: cleanerViewModel,
                selectedTab: $selectedTab
            )
                .tabItem {
                    Label("Smart Analysis", systemImage: "waveform.badge.magnifyingglass")
                }
                .tag(1)

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
                .tag(2)
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
