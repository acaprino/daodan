import ArgumentParser
import ShopKit

@main
struct Shop: ParsableCommand {
    @Option(help: "Price in cents.")
    var cents: Int = 100

    func run() throws {
        print(Price(cents: cents).formatted)
    }
}
