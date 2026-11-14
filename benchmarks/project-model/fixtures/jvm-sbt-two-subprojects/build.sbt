ThisBuild / organization := "com.example"
ThisBuild / version      := "0.1.0-SNAPSHOT"
ThisBuild / scalaVersion := "3.3.4"

lazy val root = (project in file("."))
  .aggregate(core, app)
  .settings(
    name := "ledger",
    publish / skip := true
  )

lazy val core = (project in file("core"))
  .settings(
    name := "ledger-core",
    libraryDependencies ++= Seq(
      "org.typelevel" %% "cats-core" % "2.12.0",
      "org.scalatest" %% "scalatest" % "3.2.19" % Test
    )
  )

lazy val app = (project in file("app"))
  .dependsOn(core)
  .settings(
    name := "ledger-app",
    Compile / mainClass := Some("com.example.ledger.app.Main")
  )
