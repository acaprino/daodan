"""The real public applications `modal_binding.py` measures: where they are, at which commit, under which licence. Nothing of them is in the
repository (no source, no copy): each is fetched at its commit while the Modal image is built (`https://codeload.github.com/<repository>/tar.gz/<commit>`)
and is only read there (by Noir and by Daodan's snapshot), never run, installed or built.

The licence is GitHub's SPDX id of the repository's licence file at that commit (`gh api repos/<repository>/license?ref=<commit>`, 24 November 2026),
with the file's name. `lobsters` is the exception: GitHub says NOASSERTION, the whole file was read and is the three-clause BSD licence (the third
clause names the author, not the contributors).
"""

# name -> (framework, repository, commit, licence, licence file, note)
APPS = {
    # the calibration: the Flask application of `benchmarks/flask-routes` whose answer is known (6 endpoints, all bound once the qualified name matches)
    "shhh": ("flask", "smallwat3r/shhh", "448acf4bed058d27a28a939b1ff5fba1601e2273", "MIT", "LICENSE", "calibration, as measured in flask-routes"),
    "bookstack": ("laravel", "BookStackApp/BookStack", "0326409ecde003f63f4e15cceb880a1cc0f088b2", "MIT", "LICENSE", ""),
    "koel": ("laravel", "koel/koel", "f0d5bc79d3083c6cdb335ae8a30ee565cca02a5d", "MIT", "LICENSE.md", ""),
    "rubygems": ("rails", "rubygems/rubygems.org", "6f51e324634a0820c54be2fc28533b721abadc95", "MIT", "MIT-LICENSE", ""),
    "lobsters": ("rails", "lobsters/lobsters", "d23941fd73b7a0a7280f1f40c54013b4e4db5328", "BSD-3-Clause (GitHub: NOASSERTION)", "LICENSE", ""),
    "gin-vue-admin": ("gin", "flipped-aurora/gin-vue-admin", "dcac232afb56d17c167840f69864d2765c2ca512", "Apache-2.0", "LICENSE", ""),
    "go-admin": ("gin", "go-admin-team/go-admin", "f24c303f6156f82fb626afa8f22860feefcc2ff5", "MIT", "LICENSE.md", ""),
    "go-gin-example": ("gin", "eddycjy/go-gin-example", "4f5174ca325b37f23edadad7c88d49586816a69c", "MIT", "LICENSE", ""),
    "nestjs-boilerplate": ("nestjs", "brocoders/nestjs-boilerplate", "9620f159eefe38f47747d02ab162852367c5472c", "MIT", "LICENSE", ""),
    "nest-admin": ("nestjs", "buqiyuan/nest-admin", "5b549e540d52d04f08d26ded192a455a8e4c058d", "MIT", "LICENSE", ""),
    "nestjs-realworld": ("nestjs", "mikro-orm/nestjs-realworld-example-app", "30b709d9f21aaa8bdd8f99cd04c674ae53091e3e", "MIT", "LICENSE", ""),
    "node-express-boilerplate": ("express", "hagopj13/node-express-boilerplate", "179ae84efec61b14206d0305d941daed6c6d07f9", "MIT", "LICENSE", ""),
    "anything-llm": ("express", "Mintplex-Labs/anything-llm", "593c0943facbe0a5e1cfac2d7616f15707a9317a", "MIT", "LICENSE", ""),
    "juice-shop": ("express", "juice-shop/juice-shop", "c9f99228d9d56afb5f5ca7925376292f7fa44b13", "MIT", "LICENSE", "TypeScript"),
    "litecast": ("expo-router", "dylsteck/litecast", "e73b95374d4b179ee52b4e4fc39615327ca8eb93", "MIT", "LICENSE.md", "4 `+api` modules"),
    "uni-stack": ("expo-router", "bidah/uni-stack", "96d62ca4c6d598a7887ab6d97cf50d3a5cd4bae1", "MIT", "LICENSE", "4 `+api` modules (tRPC), one per example"),
    "expo-template": ("expo-router", "mrmeg/expo-template", "4571ece79f22de7b65ee9c9cb63bb7edf4eea51f", "MIT", "LICENSE", "6 `+api` modules"),
    "petclinic": ("spring", "spring-projects/spring-petclinic", "500158f732419217507c7656904b8e6aa1bcc0d6", "Apache-2.0", "LICENSE.txt", "Java; pin of benchmarks/spring-actuator-mappings"),
    "ruoyi": ("spring", "yangzongzhuan/RuoYi", "d6708994364bfbb472c96380d6129e24303b3228", "MIT", "LICENSE", "Java; pin of benchmarks/spring-actuator-mappings"),
    "petclinic-kotlin": ("spring-kotlin", "spring-petclinic/spring-petclinic-kotlin", "9823b3aa97988854668e608750db88502775caa7", "Apache-2.0", "LICENSE", "Kotlin"),
    "eshoponweb": ("aspnet", "dotnet-architecture/eShopOnWeb", "4da8212117e87d808d4bbc7da6286fd2147ce606", "MIT", "LICENSE", "MVC controllers, Razor Pages (archived repository)"),
    "eshop": ("aspnet", "dotnet/eShop", "669682e724306a48f6c6ec4c8afea941658bf3a7", "MIT", "LICENSE", "minimal APIs"),
    "btcpayserver": ("aspnet", "btcpayserver/btcpayserver", "da4b5935c160dd057c6ad32fc92d655fbe6d5db5", "MIT", "LICENSE", "MVC controllers; the snapshot did not end in an hour (24 November 2026)"),
    "healthchecks": ("django", "healthchecks/healthchecks", "c1039ad23395162c5e2f17d324d8ccdaa60a1d14", "BSD-3-Clause", "LICENSE", "pin of benchmarks/django-routes"),
    "defectdojo": ("django", "DefectDojo/django-DefectDojo", "cd0a4483a224707f72a0fc3112359089c1446b55", "BSD-3-Clause", "LICENSE.md", "pin of benchmarks/django-routes"),
    "fastapi-template": ("fastapi", "fastapi/full-stack-fastapi-template", "77e550a73bb49dd2967622c5ed11bf7a49603c93", "MIT", "LICENSE", "pin of benchmarks/fastapi-routes/apps.py"),
    "dispatch": ("fastapi", "Netflix/dispatch", "dd2837e82a0bf5565b1b4b4b91ea30b7262d4061", "Apache-2.0", "LICENSE", "archived repository"),
}
# The Noir that `daodan/core/premap/noir.py` pins (`DOWNLOAD`): the image checks the binary's sha256 against the one below, and `summarize.py` refuses an answer
# whose `noir_pin` (Daodan's own `DOWNLOAD`) is another.
NOIR = ("https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64",
        "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70")
