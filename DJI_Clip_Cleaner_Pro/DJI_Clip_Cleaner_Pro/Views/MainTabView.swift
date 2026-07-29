import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    @StateObject private var cleanerViewModel = CleanerViewModel()

    var body: some View {
        TabView(selection: $selectedTab) {
            CleanerView(viewModel: cleanerViewModel)
                .tabItem {
                    Label("Pit Lane", systemImage: "flag.checkered")
                }
                .tag(0)

            AnalysisView(
                cleanerViewModel: cleanerViewModel,
                selectedTab: $selectedTab
            )
                .tabItem {
                    Label("Scouting", systemImage: "binoculars.fill")
                }
                .tag(1)

            SettingsView()
                .tabItem {
                    Label("Garage Setup", systemImage: "wrench.and.screwdriver.fill")
                }
                .tag(2)

            ManualView()
                .tabItem {
                    Label("Race Manual", systemImage: "book.fill")
                }
                .tag(3)
        }
        .tint(AppTheme.papaya)
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
