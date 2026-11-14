// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Shop",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "ShopKit", targets: ["ShopKit"]),
        .executable(name: "shop", targets: ["ShopCLI"]),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser.git", from: "1.5.0"),
    ],
    targets: [
        .target(name: "ShopKit"),
        .executableTarget(
            name: "ShopCLI",
            dependencies: [
                "ShopKit",
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
            ]
        ),
        .testTarget(name: "ShopKitTests", dependencies: ["ShopKit"]),
    ]
)
