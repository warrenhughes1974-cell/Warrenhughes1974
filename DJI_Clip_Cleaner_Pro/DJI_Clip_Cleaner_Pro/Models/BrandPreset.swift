import Foundation

enum BrandTitleFormat: String, CaseIterable, Identifiable, Sendable {
    case full = "Channel · Series · Hook"
    case seriesHook = "Series · Hook"
    case hookOnly = "Hook only"

    var id: String { rawValue }

    var displayName: String { rawValue }
}

/// Lifestyle / series labels for Fun Now Run Later–style channels.
/// Pick one in Settings (dropdown). Story Review still owns episode facts.
enum BrandPreset: String, CaseIterable, Identifiable, Sendable {
    case dayInTheLife = "Day In The Life"
    case familyDay = "Family Day"
    case travelDay = "Travel Day"
    case workTravel = "Work Travel"
    case roadTrip = "Road Trip"
    case cruiseDay = "Cruise Day"
    case hotelStay = "Hotel / Airbnb"
    case themeParkDay = "Theme Park Day"
    case adventureOutdoor = "Adventure / Outdoor"
    case beachDay = "Beach Day"
    case foodRestaurants = "Food & Restaurants"
    case cookingAtHome = "Cooking At Home"
    case storeWalk = "Store Walk"
    case shoppingHaul = "Shopping Haul"
    case productReview = "Product Review"
    case unboxing = "Unboxing"
    case petLife = "Pet Life"
    case halloweenHunt = "Halloween Hunt"
    case holidaySeasonal = "Holiday / Seasonal"
    case concertEvent = "Concert / Event"
    case sportsDay = "Sports Day"
    case fashionStyle = "Fashion / Style"
    case diyHome = "DIY / Home"
    case behindTheScenes = "Behind the Scenes"
    case custom = "Custom"

    var id: String { rawValue }

    var displayName: String { rawValue }

    var seriesName: String {
        self == .custom ? "" : rawValue
    }

    var sampleHook: String {
        switch self {
        case .dayInTheLife: return "Day In The Life"
        case .familyDay: return "Family Day Out"
        case .travelDay: return "Travel Day Chaos"
        case .workTravel: return "Business Trip Day"
        case .roadTrip: return "Road Trip Stop"
        case .cruiseDay: return "Cruise Day"
        case .hotelStay: return "Hotel Tour"
        case .themeParkDay: return "Park Day"
        case .adventureOutdoor: return "Outdoor Adventure"
        case .beachDay: return "Beach Day"
        case .foodRestaurants: return "Food Review"
        case .cookingAtHome: return "Home Cooked"
        case .storeWalk: return "Store Walk Discovery"
        case .shoppingHaul: return "Shopping Haul"
        case .productReview: return "Honest Product Review"
        case .unboxing: return "Unboxing First Look"
        case .petLife: return "Pet Life"
        case .halloweenHunt: return "Creepy Aisle Find"
        case .holidaySeasonal: return "Holiday Find"
        case .concertEvent: return "Event Night"
        case .sportsDay: return "Game Day"
        case .fashionStyle: return "Outfit Check"
        case .diyHome: return "DIY Project"
        case .behindTheScenes: return "Setup & B-Roll"
        case .custom: return "Your Clip Hook"
        }
    }

    /// Word viewers often pair with this series in search.
    var searchKeyword: String {
        switch self {
        case .dayInTheLife: return "vlog"
        case .familyDay: return "family"
        case .travelDay, .workTravel, .roadTrip: return "travel"
        case .cruiseDay: return "cruise"
        case .hotelStay: return "hotel"
        case .themeParkDay: return "theme park"
        case .adventureOutdoor: return "adventure"
        case .beachDay: return "beach"
        case .foodRestaurants: return "food"
        case .cookingAtHome: return "cooking"
        case .storeWalk, .shoppingHaul: return "shopping"
        case .productReview, .unboxing: return "review"
        case .petLife: return "pets"
        case .halloweenHunt: return "halloween"
        case .holidaySeasonal: return "holiday"
        case .concertEvent: return "concert"
        case .sportsDay: return "sports"
        case .fashionStyle: return "fashion"
        case .diyHome: return "diy"
        case .behindTheScenes: return "behind the scenes"
        case .custom: return "vlog"
        }
    }

    var isRetail: Bool {
        switch self {
        case .halloweenHunt, .storeWalk, .shoppingHaul, .productReview, .unboxing, .holidaySeasonal:
            return true
        default:
            return false
        }
    }

    var openingLine: String {
        switch self {
        case .dayInTheLife:
            return "A real day with us — no script, just what actually happened."
        case .familyDay:
            return "A family day out, filmed as it happened."
        case .travelDay:
            return "A full travel day — the good, the delays, and everything in between."
        case .workTravel:
            return "A work trip day on the road (and in the airports)."
        case .roadTrip:
            return "On the road for this one — stops, snacks, and the unexpected."
        case .cruiseDay:
            return "A day at sea / in port from this cruise."
        case .hotelStay:
            return "A look at where we stayed and whether it was worth it."
        case .themeParkDay:
            return "A park day — rides, food, waits, and the moments worth the ticket."
        case .adventureOutdoor:
            return "Outside for this one — trails, views, and whatever the day threw at us."
        case .beachDay:
            return "Beach day energy — sun, sand, and the real vibe."
        case .foodRestaurants:
            return "We tried this spot so you know if it is actually worth the trip."
        case .cookingAtHome:
            return "In the kitchen for this one — real cooking, real results."
        case .storeWalk:
            return "A full walk through the aisles to see what actually made it onto the shelves."
        case .shoppingHaul:
            return "Everything we bought (and what we left on the shelf)."
        case .productReview:
            return "A hands-on look after real use — no script, no sponsorship."
        case .unboxing:
            return "First look straight out of the box — honest reactions."
        case .petLife:
            return "A day in pet life — the cute, the chaos, and the treats."
        case .halloweenHunt:
            return "Halloween is creeping into the stores early this year, so we went looking for the good stuff."
        case .holidaySeasonal:
            return "Seasonal shelves are changing — here is what we found."
        case .concertEvent:
            return "An event night — the crowd, the energy, and the moments we caught."
        case .sportsDay:
            return "Game day energy — from the stands to the highlights."
        case .fashionStyle:
            return "Outfit / style look — what we wore and why."
        case .diyHome:
            return "A home project from start to (almost) finish."
        case .behindTheScenes:
            return "A look at how this one actually got made."
        case .custom:
            return "Here is what actually happened in this video."
        }
    }

    var closingLine: String {
        switch self {
        case .dayInTheLife:
            return "Watch through for how the rest of the day unfolded."
        case .familyDay:
            return "Comment what family day you want to see next."
        case .travelDay, .workTravel:
            return "Subscribe for more travel days — and tell me your worst delay story in the comments."
        case .roadTrip:
            return "Comment which road-trip stop we should film next."
        case .cruiseDay:
            return "Comment where we should sail next."
        case .hotelStay:
            return "Comment if you want more hotel / Airbnb tours."
        case .themeParkDay:
            return "Comment your favorite ride — and which park we should do next."
        case .adventureOutdoor:
            return "Comment the adventure you want to see next."
        case .beachDay:
            return "Comment your favorite beach day tip."
        case .foodRestaurants:
            return "Comment what we should eat next — and if you have tried this place."
        case .cookingAtHome:
            return "Comment what you want cooked next."
        case .storeWalk:
            return "If you want to know what is in stock before you make the trip, this covers it."
        case .shoppingHaul:
            return "Comment what you would have bought (or skipped)."
        case .productReview, .unboxing:
            return "Stay to the end for whether it is actually worth buying."
        case .petLife:
            return "Comment your pet’s name — we read them."
        case .halloweenHunt:
            return "If you are shopping for Halloween this year, this shows what is on the shelves right now, what is worth the price, and what to skip."
        case .holidaySeasonal:
            return "Comment which holiday haul you want next."
        case .concertEvent:
            return "Comment the event you want us to catch next."
        case .sportsDay:
            return "Comment your team — respectfully."
        case .fashionStyle:
            return "Comment if you want more outfit / style videos."
        case .diyHome:
            return "Comment the DIY you want to see next."
        case .behindTheScenes:
            return "Comment if you want a closer look at any part of the setup."
        case .custom:
            return "Watch through for how the day actually unfolded."
        }
    }

    func searchSnippet(hook: String, atStores: String) -> String {
        switch self {
        case .dayInTheLife:
            return "\(hook) — a real day-in-the-life from this shoot."
        case .familyDay:
            return "\(hook) — family day moments from this outing."
        case .travelDay:
            return "\(hook) — travel day story\(atStores), including the parts that did not go to plan."
        case .workTravel:
            return "\(hook) — work travel day\(atStores) with the airports, waits, and real talk."
        case .roadTrip:
            return "\(hook) — road trip stops and the story from the drive."
        case .cruiseDay:
            return "\(hook) — cruise day moments worth keeping."
        case .hotelStay:
            return "\(hook) — hotel / stay tour and whether we would claim it again."
        case .themeParkDay:
            return "\(hook) — theme park day\(atStores): rides, food, and the waits."
        case .adventureOutdoor:
            return "\(hook) — outdoor adventure from this day."
        case .beachDay:
            return "\(hook) — beach day vibes and what we actually did."
        case .foodRestaurants:
            return "\(hook) — food review\(atStores): taste, price, and honest verdict."
        case .cookingAtHome:
            return "\(hook) — home cooking from start to plate."
        case .storeWalk:
            return "\(hook) — walking the aisles\(atStores) to see what is actually on the shelves right now."
        case .shoppingHaul:
            return "\(hook) — shopping haul\(atStores): what we bought and what we skipped."
        case .productReview:
            return "\(hook) — an honest, hands-on look before you spend your money."
        case .unboxing:
            return "\(hook) — unboxing and first impressions."
        case .petLife:
            return "\(hook) — pet life moments from this day."
        case .halloweenHunt:
            return "\(hook) — Halloween decorations are already out\(atStores), and these are the finds worth the drive."
        case .holidaySeasonal:
            return "\(hook) — seasonal finds\(atStores) before they sell out."
        case .concertEvent:
            return "\(hook) — concert / event night energy."
        case .sportsDay:
            return "\(hook) — sports day highlights and the crowd."
        case .fashionStyle:
            return "\(hook) — fashion / style look from this day."
        case .diyHome:
            return "\(hook) — DIY / home project progress."
        case .behindTheScenes:
            return "\(hook) — a behind-the-scenes look at how this one came together."
        case .custom:
            return "\(hook) — the full story from this shoot."
        }
    }

    var hashtagSeeds: [String] {
        switch self {
        case .dayInTheLife: return ["dayinthelife", "vlog"]
        case .familyDay: return ["family", "familyvlog"]
        case .travelDay: return ["travel", "travelvlog"]
        case .workTravel: return ["worktravel", "businesstravel"]
        case .roadTrip: return ["roadtrip", "travel"]
        case .cruiseDay: return ["cruise", "cruiselife"]
        case .hotelStay: return ["hotel", "hotelreview"]
        case .themeParkDay: return ["themepark", "parkday"]
        case .adventureOutdoor: return ["adventure", "outdoors"]
        case .beachDay: return ["beach", "beachday"]
        case .foodRestaurants: return ["foodie", "restaurantreview"]
        case .cookingAtHome: return ["cooking", "homecooking"]
        case .storeWalk: return ["storewalk", "shopwithme"]
        case .shoppingHaul: return ["haul", "shoppinghaul"]
        case .productReview: return ["review", "honestreview"]
        case .unboxing: return ["unboxing", "firstlook"]
        case .petLife: return ["pets", "petsoftiktok"]
        case .halloweenHunt: return ["halloween", "halloweenhunt"]
        case .holidaySeasonal: return ["holiday", "seasonal"]
        case .concertEvent: return ["concert", "liveevent"]
        case .sportsDay: return ["sports", "gameday"]
        case .fashionStyle: return ["fashion", "ootd"]
        case .diyHome: return ["diy", "homeproject"]
        case .behindTheScenes: return ["behindthescenes", "bts"]
        case .custom: return []
        }
    }

    var searchTags: [String] {
        switch self {
        case .dayInTheLife:
            return ["day in the life vlog", "lifestyle vlog", "daily vlog"]
        case .familyDay:
            return ["family vlog", "family day out", "family activities"]
        case .travelDay:
            return ["travel vlog", "airport vlog", "flight day", "travel tips"]
        case .workTravel:
            return ["business travel vlog", "work trip", "airport layover"]
        case .roadTrip:
            return ["road trip vlog", "road trip stops", "driving adventure"]
        case .cruiseDay:
            return ["cruise vlog", "cruise ship tour", "cruise day"]
        case .hotelStay:
            return ["hotel tour", "airbnb tour", "hotel review"]
        case .themeParkDay:
            return ["theme park vlog", "amusement park", "park food", "ride review"]
        case .adventureOutdoor:
            return ["outdoor adventure", "hiking vlog", "nature day"]
        case .beachDay:
            return ["beach day vlog", "beach vacation", "ocean day"]
        case .foodRestaurants:
            return ["restaurant review", "food review", "was it worth it food"]
        case .cookingAtHome:
            return ["home cooking", "recipe vlog", "cooking with me"]
        case .storeWalk:
            return [
                "store walk through",
                "shop with me",
                "new arrivals in stores",
                "retail walkthrough",
                "shelf finds",
                "clearance finds"
            ]
        case .shoppingHaul:
            return ["shopping haul", "what I bought", "try on haul"]
        case .productReview:
            return [
                "honest product review",
                "hands on review",
                "is it worth it",
                "first impressions review",
                "buy or skip"
            ]
        case .unboxing:
            return ["unboxing", "first look unboxing", "new product unbox"]
        case .petLife:
            return ["pet vlog", "dog mom", "pet life"]
        case .halloweenHunt:
            return [
                "halloween store hunt",
                "halloween decorations 2026",
                "spooky season shopping",
                "halloween animatronics",
                "seasonal store walkthrough",
                "halloween haul"
            ]
        case .holidaySeasonal:
            return ["holiday haul", "seasonal shopping", "holiday decorations"]
        case .concertEvent:
            return ["concert vlog", "live event", "night out vlog"]
        case .sportsDay:
            return ["game day vlog", "sports outing", "stadium day"]
        case .fashionStyle:
            return ["outfit ideas", "style vlog", "fashion look"]
        case .diyHome:
            return ["diy project", "home improvement", "weekend project"]
        case .behindTheScenes:
            return [
                "behind the scenes",
                "creator workflow",
                "video editing setup",
                "how i film",
                "youtube creator tips"
            ]
        case .custom:
            return []
        }
    }

    func titleVariants(hook: String) -> [String] {
        switch self {
        case .dayInTheLife:
            return ["Day In The Life: \(hook)", "\(hook) — Real Day Vlog"]
        case .familyDay:
            return ["Family Day: \(hook)", "\(hook) With The Fam"]
        case .travelDay:
            return ["Travel Day: \(hook)", "\(hook) — Airport Chaos"]
        case .workTravel:
            return ["Work Trip: \(hook)", "Business Travel: \(hook)"]
        case .roadTrip:
            return ["Road Trip: \(hook)", "\(hook) On The Road"]
        case .cruiseDay:
            return ["Cruise Day: \(hook)", "\(hook) At Sea"]
        case .hotelStay:
            return ["Hotel Tour: \(hook)", "\(hook) — Stay Review"]
        case .themeParkDay:
            return ["Park Day: \(hook)", "\(hook) At The Park"]
        case .adventureOutdoor:
            return ["Adventure: \(hook)", "\(hook) Outside"]
        case .beachDay:
            return ["Beach Day: \(hook)", "\(hook) By The Water"]
        case .foodRestaurants:
            return ["Food Review: \(hook)", "Was It Worth It? \(hook)"]
        case .cookingAtHome:
            return ["Cooking: \(hook)", "Home Cooked: \(hook)"]
        case .storeWalk:
            return [
                "Store Walk: \(hook)",
                "What's New: \(hook)",
                "Aisle Find — \(hook)",
                "I Walked In and Found \(hook)"
            ]
        case .shoppingHaul:
            return ["Haul: \(hook)", "\(hook) Shopping Haul"]
        case .productReview:
            return [
                "\(hook) Review — Worth It?",
                "Honest Take: \(hook)",
                "Don't Buy \(hook) Until You Watch",
                "\(hook) First Look"
            ]
        case .unboxing:
            return ["Unboxing: \(hook)", "\(hook) First Look Unbox"]
        case .petLife:
            return ["Pet Life: \(hook)", "\(hook) With The Pets"]
        case .halloweenHunt:
            return [
                "Halloween Merch is HERE!",
                "\(hook) at the Store Already?!",
                "Spooky Season Find: \(hook)",
                "Code Orange: \(hook)",
                "I Found the BEST Halloween Decor"
            ]
        case .holidaySeasonal:
            return ["Holiday Find: \(hook)", "\(hook) Seasonal Haul"]
        case .concertEvent:
            return ["Event Night: \(hook)", "\(hook) Live"]
        case .sportsDay:
            return ["Game Day: \(hook)", "\(hook) In The Stands"]
        case .fashionStyle:
            return ["Outfit: \(hook)", "Style Check: \(hook)"]
        case .diyHome:
            return ["DIY: \(hook)", "Home Project: \(hook)"]
        case .behindTheScenes:
            return [
                "Behind the Scenes: \(hook)",
                "How I Shot \(hook)",
                "BTS — \(hook)"
            ]
        case .custom:
            return ["New Video: \(hook)", "Today's Find: \(hook)"]
        }
    }

    var scoreBoostKeywords: [String] {
        switch self {
        case .halloweenHunt: return ["halloween", "spooky", "code orange"]
        case .storeWalk, .shoppingHaul: return ["store", "aisle", "found", "haul"]
        case .productReview, .unboxing: return ["review", "worth", "unbox"]
        case .behindTheScenes: return ["behind", "bts"]
        case .travelDay, .workTravel, .roadTrip: return ["travel", "flight", "airport", "road"]
        case .themeParkDay: return ["park", "ride", "theme"]
        case .foodRestaurants, .cookingAtHome: return ["food", "taste", "recipe", "restaurant"]
        case .petLife: return ["pet", "dog", "cat"]
        case .dayInTheLife, .familyDay: return ["day", "family", "vlog"]
        default: return [searchKeyword]
        }
    }

    func storyShape(lengthNote: String) -> String {
        switch self {
        case .halloweenHunt:
            return "Curiosity → creepy reveal → open loop. \(lengthNote)"
        case .storeWalk, .shoppingHaul:
            return "Walk-up → spot the item → react / price / why it matters. \(lengthNote)"
        case .productReview, .unboxing:
            return "Claim → proof in-hand → honest verdict tease. \(lengthNote)"
        case .behindTheScenes:
            return "Setup → the interesting beat → invite to the full video. \(lengthNote)"
        case .travelDay, .workTravel:
            return "Plan → delay/obstacle → how the day turned. \(lengthNote)"
        case .themeParkDay:
            return "Arrive → ride/food highlight → reaction. \(lengthNote)"
        case .foodRestaurants:
            return "Order → first bite → honest verdict tease. \(lengthNote)"
        case .petLife:
            return "Cute open → funny chaos → soft CTA. \(lengthNote)"
        default:
            return "Hook → payoff → invite. \(lengthNote)"
        }
    }

    var musicIdeas: (mood: String, search: [String], mixTip: String) {
        switch self {
        case .halloweenHunt:
            return (
                "Yes — put tense / eerie music under it. Sparse, not a full song with vocals.",
                ["dark ambient", "horror tension", "eerie piano", "halloween suspense"],
                "Duck music under your voice (−12 to −18 dB). Let a riser hit on the reveal, then cut music for the last spoken CTA."
            )
        case .storeWalk, .shoppingHaul:
            return (
                "Yes — light upbeat or quirky shop beat behind the walk. Keep it playful.",
                ["lofi shop", "quirky ukulele", "upbeat casual", "retail vlog"],
                "Music stays low under talking. Bump it 2–3 dB in silent walking gaps, then drop again when you speak."
            )
        case .productReview, .unboxing:
            return (
                "Yes — clean modern bed, no big drops that fight your verdict.",
                ["modern corporate light", "tech review ambient", "soft electronic"],
                "Hold music flat under speech. A short hit on the product close-up is enough."
            )
        case .behindTheScenes:
            return (
                "Optional — soft ambient if the room tone is thin; skip music if tools/noise already fill it.",
                ["soft ambient", "workshop chill", "documentary bed"],
                "If you use music, keep it quieter than usual so real sound sells the BTS feel."
            )
        case .travelDay, .workTravel, .roadTrip, .cruiseDay:
            return (
                "Yes — light cinematic travel bed; keep airports/ambience audible.",
                ["travel vlog", "cinematic journey", "airport ambient soft"],
                "Voice first. Let real terminal/road sound peek through under the bed."
            )
        case .themeParkDay, .concertEvent, .sportsDay:
            return (
                "Yes — energetic but not crushing the crowd noise.",
                ["upbeat adventure", "festival energy", "stadium pop"],
                "Duck hard under speech; let crowd pops ride a little louder."
            )
        case .foodRestaurants, .cookingAtHome:
            return (
                "Yes — warm cozy kitchen / cafe bed.",
                ["cooking vlog", "cafe jazz soft", "foodie upbeat"],
                "Keep sizzles and room tone; music stays under talking."
            )
        case .petLife, .familyDay, .dayInTheLife:
            return (
                "Yes — friendly lifestyle beat.",
                ["family vlog", "feel good acoustic", "soft ukulele"],
                "Bright but quiet under voices and pet sounds."
            )
        default:
            return (
                "Yes — match the mood of the moment (tense, funny, or chill).",
                ["vlog beat", "cinematic tension", "funny comedy sting"],
                "Voice first. Music supports; it should never bury what you said."
            )
        }
    }

    var framingExtraTip: String? {
        switch self {
        case .halloweenHunt:
            return "Hold an extra half-second on the spooky item after you name it — that silence sells the scare."
        case .storeWalk, .shoppingHaul:
            return "Show the shelf tag / price if it’s readable; viewers love that detail."
        case .productReview, .unboxing:
            return "Insert one tight product insert (label, texture, button) mid-clip."
        case .behindTheScenes:
            return "If you’re talking to camera, keep eyes near the top third."
        case .foodRestaurants, .cookingAtHome:
            return "Get one clean bite / plate insert before the verdict."
        case .themeParkDay:
            return "Catch one reaction shot on the ride or after — faces sell park Shorts."
        case .petLife:
            return "Stay low at pet eye-level for the cutest frame."
        case .travelDay, .workTravel:
            return "Show a gate / board / map insert if readable — context helps."
        default:
            return nil
        }
    }

    var onScreenFallback: String {
        switch self {
        case .halloweenHunt: return "WAIT FOR IT"
        case .storeWalk, .shoppingHaul: return "FOUND THIS"
        case .productReview, .unboxing: return "HONEST TAKE"
        case .behindTheScenes: return "BEHIND THE SCENES"
        case .travelDay, .workTravel: return "TRAVEL DAY"
        case .themeParkDay: return "PARK DAY"
        case .foodRestaurants: return "TASTE TEST"
        case .petLife: return "PET LIFE"
        default: return "WATCH THIS"
        }
    }

    var endingMove: String {
        switch self {
        case .halloweenHunt:
            return "Freeze on the item, text “Full hunt on the channel,” soft whoosh out."
        case .storeWalk, .shoppingHaul:
            return "Quick zoom on the find + “More aisle finds in the full video.”"
        case .productReview, .unboxing:
            return "Hold the product, text “Full review on the channel,” don’t give the final score here."
        case .behindTheScenes:
            return "Cut to a smile / wave and “Full video linked.”"
        case .travelDay, .workTravel:
            return "End on the delay / payoff face + “Full travel day on the channel.”"
        case .themeParkDay:
            return "Ride reaction freeze + “Full park day linked.”"
        case .foodRestaurants:
            return "Last bite + “Full review on the channel.”"
        default:
            return "End on a question or unfinished beat so they tap the related long-form video."
        }
    }

    var teaser: String {
        switch self {
        case .halloweenHunt: return "One of the best finds from this Halloween hunt."
        case .storeWalk: return "A quick look at what I found walking the aisles."
        case .shoppingHaul: return "A quick look at what made the haul."
        case .productReview: return "The part of the review everyone asks about."
        case .unboxing: return "First reactions from the unboxing."
        case .behindTheScenes: return "A quick behind-the-scenes moment."
        case .travelDay, .workTravel: return "A travel-day moment from the full video."
        case .themeParkDay: return "A park-day highlight from the full video."
        case .foodRestaurants: return "The bite that decided the review."
        case .petLife: return "A pet moment from the full video."
        default: return "A quick moment from the full video."
        }
    }

    var shortHashtag: String? {
        hashtagSeeds.first.map { "#\($0)" }
    }

    var hookExtras: [String] {
        switch self {
        case .halloweenHunt: return ["spooky", "creepy aisle", "haunt"]
        case .storeWalk, .shoppingHaul: return ["aisle", "store", "walk", "haul"]
        case .productReview, .unboxing: return ["first look", "unbox", "testing"]
        case .behindTheScenes: return ["setup", "behind"]
        case .travelDay, .workTravel: return ["flight", "delay", "airport", "gate"]
        case .themeParkDay: return ["ride", "park", "line"]
        case .foodRestaurants: return ["taste", "food", "menu"]
        case .petLife: return ["dog", "cat", "pet"]
        default: return []
        }
    }

    var findExtras: [String] {
        switch self {
        case .halloweenHunt: return ["skull", "ghost", "bat", "fog", "animatronic"]
        case .storeWalk, .shoppingHaul: return ["clearance", "deal", "endcap"]
        case .productReview, .unboxing: return ["feature", "quality", "build"]
        case .behindTheScenes: return ["camera", "mic", "light"]
        case .travelDay, .workTravel: return ["boarding", "gate", "delay"]
        case .themeParkDay: return ["coaster", "queue", "pass"]
        case .foodRestaurants: return ["burger", "taco", "dessert"]
        default: return []
        }
    }

    var reactionExtras: [String] {
        switch self {
        case .halloweenHunt: return ["nightmare", "haunted", "terrifying"]
        case .storeWalk, .shoppingHaul: return ["steal", "worth it"]
        case .productReview, .unboxing: return ["recommend", "skip", "buy"]
        case .behindTheScenes: return ["done", "wrapped"]
        case .travelDay, .workTravel: return ["delayed", "stuck", "finally"]
        case .themeParkDay: return ["scream", "worth it", "so fun"]
        case .foodRestaurants: return ["delicious", "mid", "amazing"]
        default: return []
        }
    }

    var fallbackShortTitle: String {
        sampleHook
    }

    static func suggested(from folderName: String) -> BrandPreset? {
        let normalized = folderName.lowercased()

        if normalized.contains("halloween") || normalized.contains("spooky") {
            return .halloweenHunt
        }
        if normalized.contains("christmas") || normalized.contains("holiday") || normalized.contains("seasonal") {
            return .holidaySeasonal
        }
        if normalized.contains("cruise") {
            return .cruiseDay
        }
        if normalized.contains("hotel") || normalized.contains("airbnb") {
            return .hotelStay
        }
        if normalized.contains("disney") || normalized.contains("universal")
            || normalized.contains("theme") || normalized.contains("park") {
            return .themeParkDay
        }
        if normalized.contains("beach") || normalized.contains("ocean") {
            return .beachDay
        }
        if normalized.contains("hike") || normalized.contains("trail")
            || normalized.contains("adventure") || normalized.contains("outdoor") {
            return .adventureOutdoor
        }
        if normalized.contains("airport") || normalized.contains("flight")
            || normalized.contains("dfw") || normalized.contains("travel") {
            return .travelDay
        }
        if normalized.contains("work") || normalized.contains("business") || normalized.contains("omaha") {
            return .workTravel
        }
        if normalized.contains("road") || normalized.contains("drive") {
            return .roadTrip
        }
        if normalized.contains("restaurant") || normalized.contains("food")
            || normalized.contains("dinner") || normalized.contains("lunch") {
            return .foodRestaurants
        }
        if normalized.contains("cook") || normalized.contains("kitchen") || normalized.contains("recipe") {
            return .cookingAtHome
        }
        if normalized.contains("unbox") {
            return .unboxing
        }
        if normalized.contains("haul") {
            return .shoppingHaul
        }
        if normalized.contains("store") || normalized.contains("walk") || normalized.contains("aisle") {
            return .storeWalk
        }
        if normalized.contains("review") || normalized.contains("product") {
            return .productReview
        }
        if normalized.contains("pet") || normalized.contains("coco") || normalized.contains("dog") {
            return .petLife
        }
        if normalized.contains("family") || normalized.contains("gabie") || normalized.contains("domi") {
            return .familyDay
        }
        if normalized.contains("concert") || normalized.contains("event") {
            return .concertEvent
        }
        if normalized.contains("sport") || normalized.contains("game") || normalized.contains("stadium") {
            return .sportsDay
        }
        if normalized.contains("fashion") || normalized.contains("outfit") {
            return .fashionStyle
        }
        if normalized.contains("diy") || normalized.contains("home project") {
            return .diyHome
        }
        if normalized.contains("behind") || normalized.contains("bts") || normalized.contains("setup") {
            return .behindTheScenes
        }
        if normalized.contains("vlog") || normalized.contains("day in") {
            return .dayInTheLife
        }

        return nil
    }
}
