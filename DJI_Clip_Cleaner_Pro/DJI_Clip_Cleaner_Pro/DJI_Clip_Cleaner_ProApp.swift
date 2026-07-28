import SwiftUI

@main
struct DJI_Clip_Cleaner_ProApp: App {
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .frame(minWidth: 900, minHeight: 600)
        }
        .windowResizability(.contentSize)
    }
}
